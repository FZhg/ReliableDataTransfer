# How to run my code



# Verification

## Direct Link
Receiver Machine: ubuntu2004-002.student.cs.uwaterloo.ca (10.15.154.51)

Sender Machine: ubuntu2004-004.student.cs.uwaterloo.ca  (10.15.154.52)

| File Length              | The Number of Test Iterations | Sender Max-Timeout | Passed |
|--------------------------|-------------------------------|--------------------|--------|
| 8 Packets (3946 chars)   | 10                            | 400 ms             | ✅      |
| 45 Packets (22386 chars) | 1                             | 400 ms             | ✅      |


## With nEmualtor
Network Emulator Machine:  ubuntu2004-008.student.cs.uwaterloo.ca (129.97.167.27)


Receiver Machine: ubuntu2004-002.student.cs.uwaterloo.ca (10.15.154.51)

Sender Machine: ubuntu2004-004.student.cs.uwaterloo.ca  (10.15.154.52)






| File Length              | Sender Max-Timeout | nEmulator Max-Delay | nEmulator Drop Probability |
|--------------------------|--------------------|---------------------|----------------------------|
| 45 Packets (22386 chars) | 450 ms             | 100 ms              | 0.1                        |
|                          |                    |||