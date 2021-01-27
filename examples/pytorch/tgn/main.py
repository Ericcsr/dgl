import dgl
import torch
import numpy as np
from tgn import TGN
from data import TemporalWikipediaDataset,TemporalDataLoader,negative_sampler
import argparse

from sklearn.metrics import average_precision_score, roc_auc_score
# TODO: Implement negative sampling
# Only can sample from actual node id from the entire graph (masked graph)
# Negative sampling need based on current data division, which need to tell.
def train(model,dataloader,criterion,optimizer):
    model.train()
    done = False
    batch_size = dataloader.batch_size
    total_loss = 0
    while not done:
        optimizer.zero_grad()
        done,src_list,dst_list, t_stamps, subgraph = dataloader.get_next_batch(mode="train")
        neg_list = negative_sampler(dataloader.train_g,size=batch_size)
        pred_pos,pred_neg = model(src_list,dst_list,neg_list,t_stamps,subgraph,mode="train")
        loss = criterion(pred_pos,torch.ones_like(pred_pos))
        loss+= criterion(pred_neg,torch.zeros_like(pred_neg))
        total_loss += float(loss)*batch_size
        loss.backward() # May be very problematic
        optimizer.step()
        model.detach_memory()
    return total_loss/dataloader.train_g.num_edges()


def test_val(model,dataloader,criterion,mode='valid'):
    model.eval()
    done = False
    batch_size = dataloader.batch_size
    total_loss = 0
    # Metrics
    aps,aucs = [], []
    with torch.no_grad:
        while not done:
            done,src_list,dst_list,t_stamps, subgraph = dataloader.get_next_batch(mode=mode)
            neg_list = negative_sampler(dataloader.train_g,size=batch_size)
            pred_pos, pred_neg = model(src_list,dst_list,neg_list,t_stamps,subgraph,mode=mode)
            loss = criterion(pred_pos,torch.ones_like(pred_pos))
            loss+= criterion(pred_pos,torch.zeros_like(pred_neg))
            total_loss += float(loss)*batch_size
            y_pred = torch.cat([pred_pos,pred_neg],dim=0).sigmoid().cpu()
            y_true = torch.cat([torch.ones(pred_pos.size(0)),torch.ones(pred_neg.size(0))],dim=0)
            aps.append(average_precision_score(y_true,y_pred))
            aucs.append(roc_auc_score(y_true,y_pred))
    return float(torch.tensor(aps).mean()), float(torch.tensor(aucs).mean())



# TODO: define the argparser and run logic
if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--epochs",type=int,default=50,help='epochs for training on entire dataset')
    parser.add_argument("--batch_size",type=int,default=200,help="Size of each batch")
    parser.add_argument("--embedding_dim",type=int,default=100,
                        help="Embedding dim for link prediction")
    parser.add_argument("--memory_dim",type=int,default=100,
                        help="dimension of memory")
    parser.add_argument("--temporal_dim",type=int,default=100,
                        help="Temporal dimension for time encoding")
    parser.add_argument("--memory_updater",type=str,default='gru',
                        help="Recurrent unit for memory update")
    parser.add_argument("--aggregator",type=str,default='last',
                        help="Aggregation method for memory update")
    parser.add_argument("--n_neighbors",type=int,default=10,
                        help="number of neighbors while doing embedding")
    parser.add_argument("--sampling_method",type=str,default='topk',
                        help="In embedding how node aggregate from its neighor")
    parser.add_argument("--num_heads",type=int,default=8,
                        help="Number of heads for multihead attention mechanism")

    args = parser.parse_args()
    data = TemporalWikipediaDataset()

    dataloader = TemporalDataLoader(data,
                                    args.batch_size,
                                    args.n_neighbors,
                                    args.sampling_method)

    edge_dim = data.edata['feats'].shape[1]
    num_node = data.num_nodes()

    model = TGN(edge_feat_dim = edge_dim,
                memory_dim = args.memory_dim,
                temporal_dim = args.temporal_dim,
                embedding_dim= args.embedding_dim,
                num_heads = args.num_heads,
                num_nodes = num_node,
                n_neighbors = args.n_neighbors,
                memory_updater_type=args.memory_updater)
    model.attach_sampler(dataloader.get_edge_affiliation,dataloader.get_edge_affiliation)

    criterion = torch.nn.BCEWithLogitsLoss()
    optimizer  = torch.optim.Adam(model.parameters(),lr=0.0001)

    for i in range(args.epochs):
        train_loss     = train(model,dataloader,criterion,optimizer)
        val_ap,val_auc = test_val(model,dataloader,criterion,mode='valid')
        print("Epoch: {}; Training Loss: {} | Validation AP: {.3f} AUC: {.3f}".format(i,train_loss,val_ap,val_auc))
    print("========Training is Done========")
    test_ap,test_auc = test_val(model,dataloader,criterion,mode="test")
    # Test with new Nodes
    nn_test_ap,nn_test_auc = test_val(model,dataloader,criterion,mode="nn_test")
    print("Test: AP: {.3f} AUC: {.3f}".format(test_ap,test_auc))
    print("New node Test: AP: {.3f} AUC: {.3f}".format(nn_test_ap,nn_test_auc))