class Parser:
    def __init__(self, *args, **kwargs):
        import argparse

        self.parser = argparse.ArgumentParser(
            description='Request Ray-Triangle computations to the PYNQ-Z1 renderer.')

        client_info = 'client: runs on any machine that accesses the  PYNQ-Z1 renderer'
        server_info = 'server: runs the render server on the PYNQ-Z1 board'
        self.parser.add_argument(
            '--mode', 
            choices=['client', 'server'],
            help=f'Defines the execution mode: (1) {client_info}. (2) {server_info}')

        self.parser.add_argument(
            '--res',
            type=int,
            nargs=2,
            help='Resolution of the final image')

        self.parser.add_argument(
            '--psize',
            type=float,
            help='Pixel size of the image')

        self.args = self.parser.parse_args()
