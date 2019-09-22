class Parser:
    def __init__(self, *args, **kwargs):
        import argparse

        self.parser = argparse.ArgumentParser(
            description='Request Ray-Triangle computations to the Fog.')

        self.parser.add_argument(
            '--mode', 
            choices=['client', 'edge', 'master', 'node'],
            help='File containing the ray geometric information')

        self.parser.add_argument(
            '--res',
            type=int,
            nargs=2,
            help='Resolution of the final image')

        self.parser.add_argument(
            '--psize',
            type=float,
            help='Pixel size')

        self.args = self.parser.parse_args()
