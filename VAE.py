import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
from xgboost_ml import XGBRegressor


# Custom Dataset to read from Excel
class ExcelDataset(Dataset):
    def __init__(self, filepath, n_samples=1499):
        df = pd.read_excel(filepath)
        data = df.iloc[1:1 + n_samples].values  # Read n_samples rows starting from second row (skip labels)
        self.X = data[:, :-1].astype(np.float32)  # All except last column as input features
        self.E = data[:, -1].astype(np.float32)  # Last column as target

    def __len__(self):
        return len(self.X)

    def __getitem__(self, idx):
        x = self.X[idx]
        e = self.E[idx]
        return torch.tensor(x), torch.tensor(e).unsqueeze(0)  # e shaped (1,)


# Encoder network: encodes input and condition into latent variables
class Encoder(nn.Module):
    def __init__(self, input_dim=158, cond_dim=8, latent_dim=16):
        super().__init__()
        self.fc1 = nn.Linear(input_dim + cond_dim, 128)
        self.relu = nn.ReLU()
        self.fc_mu = nn.Linear(128, latent_dim)
        self.fc_logvar = nn.Linear(128, latent_dim)

    def forward(self, x, cond):
        inp = torch.cat([x, cond], dim=1)
        h = self.relu(self.fc1(inp))
        mu = self.fc_mu(h)
        logvar = self.fc_logvar(h)
        return mu, logvar


# Decoder network: decodes latent variables and condition to reconstruct input
class Decoder(nn.Module):
    def __init__(self, latent_dim=16, cond_dim=8, output_dim=158):
        super().__init__()
        self.fc1 = nn.Linear(latent_dim + cond_dim, 128)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(128, output_dim)
        self.sigmoid = nn.Sigmoid()  # outputs in [0,1]

    def forward(self, z, cond):
        inp = torch.cat([z, cond], dim=1)
        h = self.relu(self.fc1(inp))
        out = self.sigmoid(self.fc2(h))
        return out


# Encoding scalar elastic modulus to an embedding vector
def encode_property(e):
    return e.repeat(1, 8)


# Reparameterization trick for sampling latent vector z
def reparameterize(mu, logvar):
    std = torch.exp(0.5 * logvar)
    eps = torch.randn_like(std)
    return mu + eps * std


# ELBO loss: reconstruction + KL divergence
def loss_function(recon_x, x, mu, logvar):
    BCE = nn.functional.binary_cross_entropy(recon_x, x, reduction='sum')
    KLD = -0.5 * torch.sum(1 + logvar - mu.pow(2) - logvar.exp())
    return BCE + KLD


# Training loop
def train(encoder, decoder, dataloader, epochs=50, lr=0.001, device='cpu'):
    encoder.to(device)
    decoder.to(device)
    optimizer = optim.Adam(list(encoder.parameters()) + list(decoder.parameters()), lr=lr)
    encoder.train()
    decoder.train()

    for epoch in range(epochs):
        total_loss = 0
        for batch_x, batch_e in dataloader:
            batch_x = batch_x.to(device)
            batch_e = batch_e.to(device)
            cond = encode_property(batch_e).to(device)

            mu, logvar = encoder(batch_x, cond)
            z = reparameterize(mu, logvar)
            recon_x = decoder(z, cond)

            loss = loss_function(recon_x, batch_x, mu, logvar)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(dataloader.dataset)
        print(f"Epoch {epoch + 1}/{epochs}, Loss: {avg_loss:.4f}")


# Generate binary lattice representation (0s and 1s) from compression strength
def generate_lattice(decoder, encoder, compression_strength, threshold=0.5, device='cpu'):
    encoder.eval()
    decoder.eval()

    with torch.no_grad():
        input_dim = 158
        x_dummy = torch.zeros((1, input_dim), device=device)
        e_tensor = torch.tensor([compression_strength], dtype=torch.float32, device=device).unsqueeze(0)
        cond = encode_property(e_tensor)

        mu, logvar = encoder(x_dummy, cond)
        z = reparameterize(mu, logvar)
        decoded = decoder(z, cond)
        lattice = (decoded >= threshold).float()
        return lattice.cpu().squeeze(0), decoded.cpu().squeeze(0)


if __name__ == "__main__":
    filepath = 'elastic_modulus_dataset.xlsx'  # Replace with actual Excel file path

    # Load dataset
    dataset = ExcelDataset(filepath)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)

    # Instantiate model and device
    encoder = Encoder(input_dim=158)
    decoder = Decoder(output_dim=158)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    # Train CVAE
    train(encoder, decoder, dataloader, epochs=100, lr=1e-3, device=device)

    # Load full data for error checking
    df = pd.read_excel(filepath)
    data_array = df.iloc[1:1 + 1499].values
    X_full = data_array[:, :-1].astype(np.float32)
    E_full = data_array[:, -1].astype(np.float32)

    # Generate lattice for last compression strength value in dataset
    compression_strength_value = E_full[-1]
    lattice, decoded_prob = generate_lattice(decoder, encoder, compression_strength_value, device=device)
    print("Generated lattice (binary 0s and 1s):")
    print(lattice)

    # Prepare XGBoost model training data
    X = X_full[:-1]  # All except last sample features
    y = E_full[:-1]  # All except last sample compression strength

    # Scale target variable to [1, 2]
    scaler_y = MinMaxScaler(feature_range=(1, 2))
    y_scaled = scaler_y.fit_transform(y.reshape(-1, 1)).ravel()

    # Train XGBoost regressor on original features
    xgb = XGBRegressor(random_state=42, objective='reg:squarederror')
    xgb.fit(X, y_scaled)

    # Predict compression strength from generated lattice
    lattice_np = lattice.numpy().reshape(1, -1)
    pred_scaled = xgb.predict(lattice_np)
    pred_compression = scaler_y.inverse_transform(pred_scaled.reshape(-1, 1)).ravel()[0]

    # Calculate error between predicted and true compression strength
    true_compression = compression_strength_value
    mse_error = mean_squared_error([true_compression], [pred_compression])

    print(f"True compression strength: {true_compression}")
    print(f"Predicted compression strength from generated lattice: {pred_compression}")
    print(f"Mean Squared Error (MSE): {mse_error:.6f}")
