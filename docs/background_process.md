# How the Python Firewall Handles Communication

Zen uses Inter-Process Communication (IPC) to facilitate communication between threads and processes.
## Explainer on IPC

Inter-Process Communication (IPC) is a mechanism that enables processes to exchange data and synchronize their actions. In Python, IPC is crucial for coordinating tasks in multi-process applications, where processes do not share memory.

One effective method for IPC is the use of sockets, specifically Unix domain sockets, which allow for communication between processes on the same machine. Unix sockets provide a reliable and efficient means of exchanging information by enabling processes to connect, send, and receive data through a designated file path. This approach is particularly beneficial for applications that require robust inter-process communication, facilitating seamless collaboration among multiple processes.
## Why is This Necessary?

Many Python applications utilize multiple threads, and some even employ multiple processes. To minimize overhead, we implement a dedicated background process. This background process collects various statistics, detects attacks, and aggregates data from all subthreads and subprocesses. By doing so, we maintain a single connection with Aikido's servers, which helps reduce per-request delays.
## How Do We Implement This?

Upon starting the application, a background process is initiated that listens on a Unix domain socket for incoming data. This process also sends periodic heartbeats with statistics to Aikido's servers and immediately relays information regarding any detected attacks. Additionally, the background process contains configuration settings that can be fetched in real-time. If a thread or subprocess needs to access this configuration, it retrieves it from this background process at the beginning of its cycle and caches it for the duration of the request, thereby improving performance.

## What is AIKIDO_TMP_DIR?
The `AIKIDO_TMP_DIR` environment variable specifies the directory used for temporary files related to the Aikido application. By default, this variable is set to /tmp. However, users can customize it to point to a directory of their choice. The Unix domain socket file, aikido.sock, is stored in this directory to facilitate Inter-Process Communication (IPC) between processes.
