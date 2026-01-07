import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, global_mean_pool
import numpy as np

# --- SETUP ---

class ElasticModulusGCN(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = GCNConv(4, 16)
        self.conv2 = GCNConv(16, 32)
        self.conv3 = GCNConv(32, 64)
        self.conv4 = GCNConv(64, 128)
        self.conv5 = GCNConv(128, 256)
        self.fc = nn.Linear(256, 1)

    def forward(self, x, edge_index, batch):
        x = F.relu(self.conv1(x, edge_index))
        x = F.relu(self.conv2(x, edge_index))
        x = F.relu(self.conv3(x, edge_index))
        x = F.relu(self.conv4(x, edge_index))
        x = F.relu(self.conv5(x, edge_index))
        x = global_mean_pool(x, batch)  # [batch_size, 256]
        out = self.fc(x)                # [batch_size, 1]
        return out.squeeze()

# --- DATA PREPARATION HELPERS ---

from torch_geometric.data import Data, DataLoader

def adj_to_edge_index(adj):
    idx = np.array(np.nonzero(adj))
    return torch.tensor(idx, dtype=torch.long)

def create_graph_data(vertex_features, adjacency_matrix, y, batch_idx=0):
    x = torch.tensor(vertex_features, dtype=torch.float)
    edge_index = adj_to_edge_index(adjacency_matrix)
    batch = torch.full((x.size(0),), batch_idx, dtype=torch.long)
    y = torch.tensor([y], dtype=torch.float)
    return Data(x=x, edge_index=edge_index, y=y, batch=batch)

# --- EXAMPLE USAGE ---

# Suppose your dataset consists of list of lattice graphs with feature/adjacency and target E
# For demonstration: use dummy features/adjacency and random target
dataset = []
for i in range(100):  # 100 samples
    V = np.random.rand(8,4)         # 8 x 4 vertex feature matrix
    A = np.random.randint(0,2,(8,8))
    A = np.triu(A,1)                # keep it undirected/symmetric, upper triangle
    A = A + A.T
    E = np.random.uniform(1,100)    # target elastic modulus
    dataset.append(create_graph_data(V, A, E, batch_idx=i))

loader = DataLoader(dataset, batch_size=8, shuffle=True)

# --- TRAINING LOOP ---

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = ElasticModulusGCN().to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
loss_fn = nn.MSELoss()

for epoch in range(100):
    model.train()
    total_loss = 0
    for batch in loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        pred = model(batch.x, batch.edge_index, batch.batch)
        loss = loss_fn(pred, batch.y.view(-1))
        loss.backward()
        optimizer.step()
        total_loss += loss.item() * batch.num_graphs
    print(f"Epoch {epoch+1}: Loss = {total_loss / len(dataset):.5f}")
