from fTestDependencies import fTestDependencies;
fTestDependencies();

from mDebugOutput import fEnableDebugOutputForClass, fEnableDebugOutputForModule, fTerminateWithException;
try:
  import urllib;
  import cTreeServer, mHTTP;
#  fEnableDebugOutputForModule(cTreeServer);
#  fEnableDebugOutputForModule(mHTTP);
  
  from cFileSystemItem import cFileSystemItem;
  from cTreeServer import cTreeServer, cTreeNode;
  from mMultiThreading import cThread;
  
  oTreeServer = cTreeServer("Test server");
  
  oChildNode1 = oTreeServer.foCreateChild("First child (html)", "html", "Test <b>html</b>");
  oChildNode1_1 = oChildNode1.foCreateChild("First grantchild");
  oChildNode1_2 = oChildNode1.foCreateChild("Second grantchild (link target)", "text", "Text text");
  
  oChildNode2 = oTreeServer.foCreateChild("Second child (markdown)", "markdown", "Test **markdown**");
  oChildNode3 = oTreeServer.foCreateChild("Third child (link to site)", "url-link", "https://example.com");
  
  oChildNode4 = oTreeServer.foCreateChild("Fourth child (link to Second grantchild)").fLinkToNode(oChildNode1_2);
  
  oTreeServer.fMakeStatic();
  print "Server running @ %s" % oTreeServer.oURL;
  urllib.urlopen(str("http://example.com"));
  oClient = mHTTP.cHTTPClient();
  for oURL in [
    oTreeServer.oURL,
    oTreeServer.oURL.foClone(szPath = "/dxTreeData.json"),
    oTreeServer.oURL.foClone(szPath = "/stop"),
  ]:
    print "Loading page %s" % oURL;
    oResponse = oClient.fozGetResponseForURL(oURL);
    assert oResponse and oResponse.uStatusCode == 200, \
        "Unexpected response %s" % oResponse;
  print "Waiting for server to stop...";
  oTreeServer.fWait();
  print "Done.";
except Exception as oException:
  fTerminateWithException(oException);