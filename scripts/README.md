# Documentation for Waggle

## To run a COSCO development environment using Docker

```bash
# Run this at the top of the repository, not within this directory, "scripts"
./scripts/run_docker.sh
```

Confirm the Docker container is running by,
```bash
docker ps
```

> We recommend using Visual Studio Code to open up the container environment using the devcontainer plugin.

## Run Visualization
Open another terminal and run,
```bash
tensorboard --logdir ./tb/
```

> If you are using Visual Studio Code, you can simply go to "PORTS" tab and open the forwarded ports. Code does port forwarding for you to connect to the tensorboard.

## Run Your Scheduler

You can create your own scheduler under the "Scheduler" directory and load it in the main.py. Then, simply run,

```bash
# mywaggle.yaml contains information
# about the host cluster, workloads, and scheduler
python3 main.py -c mywaggle.yaml
```

__NOTE: We are working on improving the framework. Some of the variables in the yaml may not work in the framework.__