# Freifunk Firmware Upgrade Allow

Script to generate htaccess rules for firmware download regulations.

A spanning tree is calculated on the, hopglass provided, network graph,
rooting in given start nodes. Nodes are whitelisted for firmware download
by applied whitelist mechanism.

### Example Execution

    ./upgrade.py -c config.json miauEnforce 

### Configuration

See ''config.json.example''.


## Available whitelist mechanisms

### miauEnforce

    min-distance: Minimal distance to starting nodes.

A mechanism meant to verify miau enforced firmware deployment. Only nodes
in minimal distance to the starting node or with up to date firmware
are whitelisted. Hence all nodes not in direct neighborhood of
the starting nodes are forced to use the miau proxy mechanism.

### outerToInnerUpgrade

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
