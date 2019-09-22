# heterogeneous-raytracing-pynq

This repository was created to provide the code to the paper "Um Sistema Heterogêneo Embarcado para
Aceleração de Interseção Raio-Triângulo" (An Embedded Heterogeneous Acceleration System for Ray-Triangle Intersections). The code provided is the state of the original code at the publishing time. 
The repository already contains the binaries and biststream needed to run the system on the PYNQ-Z1 board from Digilent.

There are basically 2 execution modes for this software. First is the 'client' mode where you run the client application. It can be any machine with network access to the PYNQ board.

## Client Mode

To execute it in client mode you need 2 things: setup the case info in the file settings/client.json. There you'll be able to configure the output image file name, the mesh to be rendered and the ip address (and port) opened on the PYNQ board. Here's the 'client.json' file:

```
{
    "client" : {
        "output" : "output.png",
        "mesh"   : "examples/bunny_2k.obj"
    },

    "edge" : {
        "ip"   : "localhost",
        "port" : 5002,
        "bitstream" : "/home/xilinx/adrianno/intersect_fpga_x2.bit"
    }
}
```

Then you just need to run the file `renderer.py`. 

```sh
python renderer.py --mode client --res 200 200 --psize 0.4
```

## Server Mode

The server mode runs on the PYNQ-Z1 board. To run it, you first need to specify the address and port bound to the server and the FPGA bitstream on 'settings/server.json'. In the same file is possible to define the resources being used by the board as well as the workload division factor. Note that the load must be smaller than 1.0, which is 100% of  workload to the FPGA. In the file there are comments that describe the hardware modes. The file 'server.json' is shown below:

```
{
    "edge" : {
        "ip"   : "",
        "port" : 5002,
        "bitstream" : "settings/intersect_fpga_x2.bit"
    },

    "processing" : {
        "_comment" : "3 modes: fpga, cpu and heterogeneous",
        "mode" : "cpu",
        "cpu" : {
            "_comment" : "cpu has 3 modes: python, singlecore and multicore",
            "mode" : "multicore"
        },
        "fpga" : {
            "_comment" : "fpga has 2 modes: single and multi",
            "mode" : "multi"
        },
        "heterogeneous" : {
            "fpga-load" : 0.4
        }
    }
}
```



After the configuration is complete, you just need to run:

```sh
sudo python3.6 renderer.py --mode server
``` 

##