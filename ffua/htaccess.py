def htAllowNode(node,output):
    print(f"# { node['nodeinfo']['hostname'] }",file=output)
    print(f"# { node['nodeinfo']['software']['firmware']['release'] }",file=output)
    if "autoupdater" in node['nodeinfo']['software']:
        if "branch" in node['nodeinfo']['software']['autoupdater']:
            print(f"# { node['nodeinfo']['software']['autoupdater']['branch'] }",file=output)
    for address in node['nodeinfo']['network']['addresses']:
        print(f"allow from { address }",file=output)

def generateHtAccessRules(generator,output):
    
    print("order deny,allow",file=output)
    num = 0
    for nodedata in generator:
        try:
            htAllowNode(nodedata,output)
            num = num + 1
        except:
            pass
    print("deny from all",file=output)
    print(f"#Allowed nodes: { num }",file=output)
