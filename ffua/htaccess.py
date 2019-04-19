def htAllowNode(node,output):
    print(f"# { node['nodeinfo']['hostname'] }",file=output)
    print(f"# { node['nodeinfo']['software']['firmware']['release'] }",file=output)
    if "autoupdater" in node['nodeinfo']['software']:
        if "branch" in node['nodeinfo']['software']['autoupdater']:
            print(f"# { node['nodeinfo']['software']['autoupdater']['branch'] }",file=output)
    for address in node['nodeinfo']['network']['addresses']:
        print(f"allow from { address }",file=output)

def generateHtAccessRulesForBranches(generator,config):
    generator = list(generator)
    for branch in config.branches.values():
        htaccess_path = branch.getSysupgradePath() / ".htaccess"
        with open(htaccess_path,"w") as output:
            generateHtAccessRules(generator, config.nets, output)

def generateHtAccessRules(generator, nets, output):
    
    print("order deny,allow",file=output)
    num = 0
    for nodedata in generator:
        try:
            htAllowNode(nodedata,output)
            num = num + 1
        except:
            pass
    if len(nets) == 0:
        print("deny from all",file=output)
    else:
        for net in nets:
            print(f"deny from { net }",file=output)
    print(f"#Allowed nodes: { num }",file=output)
