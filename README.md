# Freifunk Firmware Upgrade Allow

Simple script to generate htaccess rules for firmware download regulations.

A spanning tree is calculated on the, hopglass provided, network graph,
rooting in given start nodes. Nodes are whitelisted for firmware download
by applied whitelist mechanism.

### Example Execution

    ./upgrade.py -c config.json miauEnforce -d 1 2018.1.4~ngly-606

### Configuration

See ''config.json.example''.

## Available whitelist mechanisms

### miauEnforce

    miauEnforce [--min-distance/-d <distance>]

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

A simple logging parser and upgrade path verificaton utility. 
Is able to parse a special log format, defined by the following
Apache 2.4 configuration statements:

    LogFormat "%h \"%r\" %>s %b" firmware
	  CustomLog ${APACHE_LOG_DIR}/firmware.log firmware

The verify command reads a given set of logs and verifies for each update that
the network graph is still connected after removeing that updating node. This
is mainly designed to verify the functionality of outerToInnerUpgrade for given
configuration.
