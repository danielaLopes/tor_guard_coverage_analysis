import subprocess
import requests
import shlex
import traceback
import time
import threading
from stem import CircStatus
from stem.control import Controller
import stem.process
import stem.descriptor.remote
from retrying import retry
import os
import shutil
from flask import Flask
import sys


BASE_DIR = 'data'
SOCKS_PORT = 9050
CONTROL_PORT = 9051
ONION_SERVICE_FOLDER = 'onion_service/'
WEB_PORT = 8080


app = Flask(__name__)

@app.route('/')
def index():
    return "<h1>Hi Grandma!</h1>"

def start_web_app():
    app.run(port=WEB_PORT)


def get_onion_service_introduction_points(controller, onion_url):
    try:
        onion_name = onion_url.split('.onion')[0]
        print("onion_name", onion_name)
        desc = controller.get_hidden_service_descriptor(onion_name)

        #print(f"{onion_url}'s introduction points are...")
        #print("desc", desc)
        #for introduction_point in desc.introduction_points():
        #    print('  %s:%s => %s' % (introduction_point.address, introduction_point.port, introduction_point.identifier))

        intro_points = []

        response = controller.get_info("hsdir/{}/intro/rendezvous/current".format(onion_name))
        print("response", response)
        # Send GETINFO request to fetch introduction points
        # response = controller.get_info("hs/service/{}/rendezvous/current-intro".format(onion_name))
        # print("---- response", response)
        # if response and "hs/service/{}/rendezvous/current-intro/{}".format(onion_name, 0) in response:
        #     # Parse the response to extract introduction point information
        #     for i in range(0, len(response), 3):
        #         intro_point = response["hs/service/{}/rendezvous/current-intro/{}".format(onion_name, i)]
        #         intro_points.append(intro_point)
                
        return controller.get_network_statuses([onion_url])[0].fingerprint
    except Exception as e:
        print("Error getting onion service fingerprint:", e)
        return None
    

def stop_tor():
    command = "sudo pkill tor"
    tor_process = subprocess.Popen(shlex.split(command))
    return tor_process


def start_tor():
    command = "/opt/homebrew/opt/tor/bin/tor -f data/torrc"
    tor_process = subprocess.Popen(shlex.split(command))
    return tor_process


def generate_client_circuits(num_clients):
    # Has to be Control Port
    #with Controller.from_port() as controller:
    with Controller.from_port(port=CONTROL_PORT) as controller:
    #with Controller.from_port(address="127.0.0.1", port=CONTROL_PORT) as controller:
        controller.authenticate()
        print("Successfully authenticated with Tor control port")

        # Create a hidden service where visitors of port 80 get redirected to local
        # port 5000 (this is where Flask runs by default).

        print(" * Creating our hidden service in %s" % ONION_SERVICE_FOLDER)
        #result = controller.create_hidden_service(ONION_SERVICE_FOLDER, 80, target_port=WEB_PORT)
        result = controller.create_ephemeral_hidden_service({80: WEB_PORT}, await_publication = True)

        if result is None:
            print("Could not create hidden service. Exiting ...")
            sys.exit(0)

        print("result", result)

        # The hostname is only available when we can read the hidden service
        # directory. This requires us to be running with the same user as tor.
        onion_url = None
        if result.service_id:
            onion_url = result.service_id + '.onion'
            print(" * Our service is available at %s, press ctrl+c to quit" % onion_url)
        else:
            print(" * Unable to determine our service's hostname, probably due to being unable to read the hidden service directory")

        try:
            # Starting onion service app as a background thread
            t = threading.Thread(target=start_web_app)
            t.daemon = True
            t.start()
            
            time.sleep(10)

            # print(f"Connecting to onion url {onion_url}")
            # onion_fingerprint = get_onion_service_introduction_points(controller, onion_url)
            # print(f"Onion fingerprint {onion_fingerprint}")


            # circuit_id = controller.new_circuit()
            # print("circuit_id", circuit_id)
            # circuit_id = controller.extend_circuit(circuit_id, [result.service_id])
            # print("circuit_id 2", circuit_id)


            circuit_id = controller.new_circuit()

            # # Attach the circuit to the Onion Service
            controller.attach_stream(stream.id, circuit_id)
            #controller.attach_stream_to_circuit(stream_id, circuit_id)

            # Connect to the Onion Service
            controller.extend_circuit(circuit_id, [onion_url + ':' + str(WEB_PORT)])

            # for client_id in range(num_clients):
            #     print("=== Client {}".format(client_id))
            #     create_new_circuit(controller, client_id, onion_fingerprint)
        finally:
            # Shut down the hidden service and clean it off disk. Note that you *don't*
            # want to delete the hidden service directory if you'd like to have this
            # same *.onion address in the future.
            print(" * Shutting down our hidden service")
            controller.remove_hidden_service(ONION_SERVICE_FOLDER)
            #stop_tor()
        
        
        #except stem.CircuitExtensionFailed as e:
            
        # except Exception as e:
        #     traceback.print_exc()

        # finally:
        #     controller.signal("SHUTDOWN") # Stops the Tor process gracefully
        #     print("Exited Tor process cleanly 2")



if __name__ == "__main__":
    #stop_tor()
    # Start Tor process in the background
    #tor_process = start_tor()

    #time.sleep(20) # Wait until Tor process has started

    num_clients = 10
    generate_client_circuits(num_clients)
