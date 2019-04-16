# Freifunk Firmware Upgrade Allow

Simple script to generate htaccess rules for firmware download regulations.

A spanning tree is calculated on the, hopglass provided, network graph,
rooting in given start nodes. Nodes are whitelisted for firmware download
by applied whitelist mechanism.

### Example Execution

    ./upgrade.py -c config.json -o /path/to/sysupgrade/.htaccess miauEnforce -d 1 2018.1.4~ngly-606

### Configuration

See ''config.json.example''.

## Available whitelist mechanisms

### miauEnforce

    miauEnforce [--min-distance/-d <distance>] <firmware-version>   

A mechanism meant to verify miau enforced firmware deployment. Only nodes
that are direct neighbors of the starting node or have the targeted firmware
version are whitelisted. Hence all nodes not in direct neighborhood of
the starting nodes are forced to use miaus proxy mechanism.

### outerToInnerUpgrade

    outerToInnerUpgrade

A mechanism meant to deploy mesh breaking technology changes. Only the leafs of 
the spanning tree are allowed to download firmware, which will remove them from
the mesh network, but leaving any not upgraded node in the spanning tree.


## LogRead

A simple logging parser and reader. Is able to parse a special log output format, only.
We, Freifunk Kiel, have the following format option in our Apache 2.4 configuration:

    LogFormat "%h \"%r\" %>s %b" firmware
	  CustomLog ${APACHE_LOG_DIR}/firmware.log firmware
  
