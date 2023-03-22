# How to run my code



# Verification

## Direct Link
Receiver Machine: ubuntu2004-002.student.cs.uwaterloo.ca (10.15.154.51)

Sender Machine: ubuntu2004-004.student.cs.uwaterloo.ca  (10.15.154.52)

| File Length              | The Number of Test Iterations | Sender Max-Timeout | Final Timestamp |
|--------------------------|-------------------------------|--------------------|-----------------|
| 45 Packets (22386 chars) | 10                            | 400 ms             | 92              |


## With nEmualtor
Network Emulator Machine:  ubuntu2004-008.student.cs.uwaterloo.ca (129.97.167.27)

Receiver Machine: ubuntu2004-002.student.cs.uwaterloo.ca (10.15.154.51)

Sender Machine: ubuntu2004-004.student.cs.uwaterloo.ca  (10.15.154.52)



| File Length              | Sender Max-Timeout | nEmulator Max-Delay | nEmulator Drop Probability | Final Time Stamp |
|--------------------------|--------------------|---------------------|----------------------------|------------------|
| 45 Packets (22386 chars) | 450 ms             | 100 ms              | 0.1                        | 5008             |
| 45 Packets (22386 chars) | 500 ms             | 20 ms               | 0.2                        ||