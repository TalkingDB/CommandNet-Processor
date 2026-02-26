import socket
import time


def commandProcessorHit(arg):
    """
    Function to hit command processor socket
    to fetch NER response
    """

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Use correct port
        s.connect(("127.0.0.1", 5006))

        # Send as bytes
        s.sendall(arg.encode("utf-8"))

        buf = b""   # bytes buffer

        # Receive response
        while True:
            chunk = s.recv(4096)

            if not chunk:
                break
            else:
                buf += chunk

        s.close()

        # Convert back to string
        return buf.decode("utf-8", errors="ignore")

    except Exception as e:
        print("Error:", e)
        return None


# Speed test
t1 = time.time()

for i in range(1000):
    reply = commandProcessorHit("large cheese pizza")

t2 = time.time()

print("Time taken:", t2 - t1)

print("Last response:")
print(reply)