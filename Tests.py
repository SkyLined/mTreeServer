import os, sys;

sModuleFolder = os.path.dirname(__file__);
sBaseFolder = os.path.dirname(sModuleFolder);
sys.path.append(sBaseFolder);

from cTreeServer import cTreeServer;

oTreeServer = cTreeServer("Test server", "markdown", "Test *markdown*");
oTreeServer.fStart();

oChildNode1 = oTreeServer.foCreateChildNode("First child", "html", "Test <b>html</b>");
oChildNode1_1 = oChildNode1.foCreateChildNode("First grantchild");
oChildNode1_2 = oChildNode1.foCreateChildNode("Second grantchild");

oChildNode2 = oTreeServer.foCreateChildNode("Second child");

print "Server @ %s" % oTreeServer.sURL;

oTreeServer.fWait();
