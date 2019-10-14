import os, sys;

sModuleFolder = os.path.dirname(__file__);
sBaseFolder = os.path.dirname(sModuleFolder);
sys.path.append(sBaseFolder);
from mDebugOutput import fShowFileDebugOutputForClass;
from cFileSystemItem import cFileSystemItem;
fShowFileDebugOutputForClass(cFileSystemItem);
from cTreeServer import cTreeServer, cTreeNode;
from mMultiThreading import cThread;

def fMain():
  oTreeServer = cTreeServer("Test server");
  oTreeServer.fStart();
  
  oChildNode1 = oTreeServer.foCreateChild("First child (html)", "html", "Test <b>html</b>");
  oChildNode1_1 = oChildNode1.foCreateChild("First grantchild");
  oChildNode1_2 = oChildNode1.foCreateChild("Second grantchild (link target)", "text", "Text text");
  
  oChildNode2 = oTreeServer.foCreateChild("Second child (markdown)", "markdown", "Test **markdown**");
  oChildNode3 = oTreeServer.foCreateChild("Third child (link to site)", "link", "https://example.com");
  
  oChildNode4 = oTreeServer.foCreateChild("Fourth child (link to Second grantchild)").fLinkToNode(oChildNode1_2);
  
  oTreeServer.fMakeStatic();
  print "Server @ %s" % oTreeServer.sURL;
  
  oTreeServer.fWait();

cThread(fMain).fStart();