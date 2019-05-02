import logging

def htAllowNode(node,output):
    print(f"# { node.getHostname() }",file=output)
    print(f"# { node.getFirmwareVersion() }",file=output)
    branch = node.getBranch()
    if branch is not None:
        print(f"# { branch }",file=output)
    for address in node.getAddresses():
        print(f"allow from { address }",file=output)

def generateHtAccessRulesForBranch(branch,generator,config):
    branch = config.branches[branch]
    htaccess_path = branch.getSysupgradePath() / ".htaccess"
    with open(htaccess_path,"w") as output:
        generateHtAccessRules(generator, config.nets, output)

def generateHtAccessRulesForBranches(generator,config):
    generator = list(generator)
    for branch in config.branches:
        generateHtAccessRulesForBranch(branch,generator,config)

def generateHtAccessRules(generator, nets, output):
    
    print("order deny,allow",file=output)
    num = 0
    for nodedata in generator:
        try:
            htAllowNode(nodedata,output)
            num = num + 1
        except Exception as e:
            logging.exception(e)
    if len(nets) == 0:
        print("deny from all",file=output)
    else:
        for net in nets:
            print(f"deny from { net }",file=output)
    print(f"#Allowed nodes: { num }",file=output)
