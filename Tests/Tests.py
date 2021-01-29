from fTestDependencies import fTestDependencies;
fTestDependencies();

try:
  import mDebugOutput;
except:
  mDebugOutput = None;
try:
  try:
    from oConsole import oConsole;
  except:
    import sys, threading;
    oConsoleLock = threading.Lock();
    class oConsole(object):
      @staticmethod
      def fOutput(*txArguments, **dxArguments):
        sOutput = "";
        for x in txArguments:
          if isinstance(x, (str, unicode)):
            sOutput += x;
        sPadding = dxArguments.get("sPadding");
        if sPadding:
          sOutput.ljust(120, sPadding);
        oConsoleLock.acquire();
        print sOutput;
        sys.stdout.flush();
        oConsoleLock.release();
      fPrint = fOutput;
      @staticmethod
      def fStatus(*txArguments, **dxArguments):
        pass;
  
  import sys, urllib;
  from mHTTP import cHTTPClient;
  from cFileSystemItem import cFileSystemItem;
  from cTreeServer import cTreeServer, cTreeNode;
  from mMultiThreading import cThread;
  
  for sArgument in sys.argv[1:]:
    if sArgument == "--debug":
      assert mDebugOutput, \
          "mDebugOutput module is not available";
      mDebugOutput.fEnableDebugOutputForClass(cTreeServer);
      mDebugOutput.fEnableDebugOutputForClass(cTreeNode);
    else:
      raise AssertionError("Unknown argument %s" % sArgument);
  
  
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
  oClient = cHTTPClient();
  for oURL in [
    oTreeServer.oURL,
    oTreeServer.oURL.foClone(s0zPath = "/dxTreeData.json"),
    oTreeServer.oURL.foClone(s0zPath = "/stop"),
  ]:
    print "Loading page %s" % oURL;
    oResponse = oClient.fo0GetResponseForURL(oURL);
    assert oResponse and oResponse.uStatusCode == 200, \
        "Unexpected response:\n%s" % oResponse.fsSerialize();
  print "Waiting for server to stop...";
  oTreeServer.fWait();
  print "Done.";
except Exception as oException:
  if mDebugOutput:
    mDebugOutput.fTerminateWithException(oException, bShowStacksForAllThread = True);
  raise;
