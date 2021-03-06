import socket
import argparse
import sys
import os
from cswarmd import csock

#might be removed:
import libnacl
from libnacl import secret

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def genKey():
    box = libnacl.secret.SecretBox()
    return box.sk #return the created secret key

def handle_encrypt(args):
    inHost, inPort = args.eIn.split(':')
    outHost, outPort = args.eOut.split(':')
    box = handle_key_input(args)
    esock = csock.EncryptSock(inHost=inHost, inPort=int(inPort), outHost=outHost, outPort=int(outPort), box=box)
    esock.open()

def handle_decrypt(args):
    inHost, inPort = args.dIn.split(':')
    outHost, outPort = args.dOut.split(':')
    box = handle_key_input(args)
    dsock = csock.DecryptSock(inHost=inHost, inPort=int(inPort), outHost=outHost, outPort=int(outPort), box=box)
    dsock.open()

def handle_key_input(args):
    key = None
    if(args.key_file != None):
        if args.gen_key:
            key = genKey()
            if os.path.exists(args.key_file):
                eprint("ERROR: keyfile exists, will not overwrite")
                sys.exit(4)
            with open(args.key_file, "wb") as keyFile:
                keyFile.write(key)
            print("New key written to file: ", args.key_file)
            sys.exit(0)
        else:
            with open(args.key_file, "rb") as keyFile:
                key = keyFile.read()
    else:
        if(args.gen_key):
            eprint("ERROR: --gen-key withou --key-file not supported")
            parser.print_help()
            sys.exit(3)
        else:
            eprint("ERROR: --key-file must be specified or messages from this server will be 'impossible' to decrypt")
            sys.exit(1)
    return libnacl.secret.SecretBox(key)

def main():
    parser = argparse.ArgumentParser(description='general purpose sockets based cryptographic daemon', add_help=False)

    general_group = parser.add_argument_group('General')
    general_group.add_argument('-h', '--help', action='help', help='show this help message and exit')
    general_group.add_argument('-k', '--key-file', action='store', default=None, help='location of the keyfile for SecretBox')
    general_group.add_argument('--gen-key', action='store_true', default=None, help='generate a keyfile and then exit, requires --key-file')

# not sure if sub-parsers is the best way to handle this, but it works for now and will build well into a propper daemon later on
# so WIP? and end fate TBD
    ioParsers = parser.add_subparsers(help='subcommand verbs to control the flow of data through the daemon', dest='command')

    encryptParser = ioParsers.add_parser('e', help='take plain data stream and output encrypted stream')
    encryptParser.add_argument('--in', action='store', required=True, help='format = {host}:{port}', dest='eIn')
    encryptParser.add_argument('--out', action='store', required=True, help='format = {host}:{port}', dest='eOut')
    encryptParser.set_defaults(func=handle_encrypt)

    decryptParser = ioParsers.add_parser('d', help='take in an encrypted stream and decrypt it')
    decryptParser.add_argument('--in', action='store', required=True, help='format = {host}:{port}', dest='dIn')
    decryptParser.add_argument('--out', action='store', required=True, help='format = {host}:{port}', dest='dOut')
    decryptParser.set_defaults(func=handle_decrypt)

    args = parser.parse_args()
    
    if args.gen_key: # check to see if this is a simple --gen-key call, bail and send it to the handler if it is.
        handle_key_input(args)

    if args.command:
        args.func(args)
    else:
        eprint("nothing to due, exiting...")


if __name__ == '__main__':
    main()
