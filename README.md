# How to run my code
In the root directory, run the following cmd to start the sender and the receiver

```commandline
./sender <forward_recv_address> <forward_recv_port> <sender_recv_port> <max_timeout> <filename>
```

```commandline
./receiver <backward_recv_address> <backward_recv_port> <receiver_recv_port>  <file>
```

The log files will be generated in `RDTReceiver` and `RDTSender` directories.


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
| 45 Packets (22386 chars) | 450 ms             | 100 ms              | 0.1                        | 116              |
| 45 Packets (22386 chars) | 450 ms             | 100 ms              | 0.5                        | 306              |
| 45 Packets (22386 chars) | 450 ms             | 200 ms              | 0.1                        | 99               |
| 45 Packets (22386 chars) | 450 ms             | 300 ms              | 0.1                        | 111              |
| 45 Packets (22386 chars) | 450 ms             | 500 ms              | 0.1                        | 163              |