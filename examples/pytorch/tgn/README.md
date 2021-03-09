# Temporal Graph Neural Network (TGN)

## DGL Implementation of tgn paper.

This DGL examples implements the GNN mode proposed in the paper [TemporalGraphNeuralNetwork](https://arxiv.org/abs/2006.10637.pdf)

## TGN implementor

This example was implemented by [Ericcsr](https://github.com/Ericcsr) during his SDE internship at the AWS Shanghai AI Lab.

## Graph Dataset

Jodie Wikipedia Temporal dataset. Dataset summary:

- Num Nodes: 9227
- Num Edges: 157, 474
- Num Edge Features: 172
- Edge Feature type: LIWC
- Time Span: 30 days
- Chronological Split: Train: 70% Valid: 15% Test: 15%

Jodie Reddit Temporal dataset. Dataset summary:

- Num Nodes: 11,000
- Num Edges: 672, 447
- Num Edge Features: 172
- Edge Feature type: LIWC
- Time Span: 30 days
- Chronological Split: Train: 70% Valid: 15% Test: 15%

## How to run example files

In tgn folder, run

**please use `train.py` **

```python
python train.py --dataset wikipedia
```

If you want to use GPU, run:

```python
python train.py --dataset wikipedia
```

If you want to run in fast mode:

```python
python train.py --dataset wikipedia --fast_mode
```

If you want to change memory updating module:

```python
python train.py --dataset wikipedia --memory_updater [rnn/gru]
```

## Performance

#### Without New Node in test set

| Models/Datasets | Wikipedia         | Reddit          |
| --------------- | ----------------- | --------------- |
| TGN fast mode   | AP:96.3 AUC: 96.5 | AP:N/A AUC: N/A |
| TGN             | AP:98.9 AUC:98.5  | AP:N/A AUC: N/A |

#### With New Node in test set

| Models/Datasets | Wikipedia          | Reddit           |
| --------------- | ------------------ | ---------------- |
| TGN fast mode   | AP: 94.1 AUC:94.1  | AP: N/A AUC: N/A |
| TGN             | AP:98.2  AUC: 98.1 | AP: N/A AUC: N/A |

### Details explained

**What is Fast Mode**

Normally temporal encoding need each node uses incoming time frame as current time which might lead to two nodes have multiple interactions within the same batch need to maintain multiple embedding features which slow down the batching process to avoid feature duplication, fast mode enable fast batching since it uses last memory update time in last batch as temporal encoding benchmark for each node. Also within each batch, all interaction between two nodes are predicted using same set of enbedding feature

**What is New Node test**

To test the model has the ability to predict link between unseen nodes based on neighboring information of seen nodes. This model deliberately select 10 % of node in test graph and mask them out during the training
