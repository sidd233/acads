## Experiment 6: PRE vs POST-ReLU, Conv2 filter 3
| Rank | PRE idx | PRE digit | S_pre | PRE loc | POST idx | POST digit | S_post | POST loc |
|---|---|---|---|---|---|---|---|---|
| 1 | 506 | 3 | 18.0657 | (0,3) | 506 | 3 | 18.0657 | (0,3) |
| 2 | 1149 | 5 | 18.0431 | (0,6) | 1149 | 5 | 18.0431 | (0,6) |
| 3 | 535 | 0 | 17.9810 | (6,3) | 535 | 0 | 17.9810 | (6,3) |
| 4 | 983 | 3 | 17.9751 | (0,3) | 983 | 3 | 17.9751 | (0,3) |
| 5 | 1342 | 2 | 17.6932 | (7,6) | 1342 | 2 | 17.6932 | (7,6) |
| 6 | 1194 | 7 | 17.5969 | (0,2) | 1194 | 7 | 17.5969 | (0,2) |
| 7 | 302 | 3 | 17.5920 | (0,2) | 302 | 3 | 17.5920 | (0,2) |
| 8 | 1499 | 5 | 17.5793 | (0,3) | 1499 | 5 | 17.5793 | (0,3) |

- Top-8 image sets identical: True; locations identical for shared images: True
- Images whose PRE-ReLU maximum is negative (so S_post = 0): 20 of 2000
- Min S_pre over all images: -0.5686; Top-8 S_pre all positive: True
- Images with S_post = 0 (tied at zero): 20

Lowest-scoring images (least-negative PRE max is still negative; POST clamps to 0):
| Rank from bottom | idx | digit | S_pre | S_post | loc of PRE max |
|---|---|---|---|---|---|
| 1 | 1195 | 1 | -0.5686 | 0.0000 | (3,1) |
| 2 | 1631 | 1 | -0.5361 | 0.0000 | (3,6) |
| 3 | 1061 | 1 | -0.4972 | 0.0000 | (7,5) |
| 4 | 479 | 1 | -0.4930 | 0.0000 | (7,3) |
| 5 | 1993 | 1 | -0.3780 | 0.0000 | (7,1) |
| 6 | 915 | 1 | -0.3759 | 0.0000 | (7,1) |
| 7 | 1532 | 1 | -0.2970 | 0.0000 | (3,6) |
| 8 | 1240 | 1 | -0.2714 | 0.0000 | (7,1) |
