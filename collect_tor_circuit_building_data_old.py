# Methodology was based on Section 6.2 of paper "Quantifying measurement quality and load distribution in Tor": https://dl.acm.org/doi/pdf/10.1145/3427228.3427238

# I can always create a new container image with a Tor process representing each client and it will always choose a new guard node, so I don't have to change the default Tor definitions
# Log all relays along with their data, specifically geographical location, used in each client circuit.
# In the paper, the authors logged over 8.6 million circuits, representing about 275,000 circuits per day
# Drop the circuit immediately after creation to ensure not overloading the guard relays
# Wait 16 minutes between each circuit

import subprocess
import traceback


BASE_DIR = 'data'



def load_tor_client_image():
    try:
        command = "docker pull torproject/tor"
        subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
        print(f"Created torproject/tor image")
    except subprocess.CalledProcessError as e:
        print(f"Error pulling torproject/tor image")
        traceback.print_exc()


def generate_client_circuit(client_id):
    try:
        command = f"docker run -it --name tor-client{client_id} -v $PWD/{BASE_DIR}:/app torproject/tor"
        subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
        print(f"Created tor-client{client_id} container")
    except subprocess.CalledProcessError as e:
        print(f"Error creating tor-client{client_id} container")
        traceback.print_exc()

    try:
        command = f"docker exec tor-client{client_id} tor -q -c /etc/tor/torrc -l /var/log/tor/circuits.log"
        result = subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command in Docker container: {e}")
        traceback.print_exc()

    try:
        command = f"docker exec tor-client{client_id} cp /var/log/tor/circuits.log /app/circuits_{client_id}.log"
        result = subprocess.run(command, capture_output=True, text=True, shell=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command in Docker container: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    load_tor_client_image()
    generate_client_circuit()