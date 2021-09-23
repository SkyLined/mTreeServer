from fTestDependencies import fTestDependencies;
fTestDependencies();

try: # mDebugOutput use is Optional
  import mDebugOutput as m0DebugOutput;
except ModuleNotFoundError as oException:
  if oException.args[0] != "No module named 'mDebugOutput'":
    raise;
  m0DebugOutput = None;

guExitCodeInternalError = 1; # Use standard value;

try: # mSSL use is optional
  import mSSL as m0SSL;
except ModuleNotFoundError as oException:
  if oException.args[0] != "No module named 'mSSL'":
    raise;
  m0SSL = None;

try:
  try:
    from mConsole import oConsole;
  except:
    import sys, threading;
    oConsoleLock = threading.Lock();
    class oConsole(object):
      @staticmethod
      def fOutput(*txArguments, **dxArguments):
        sOutput = "";
        for x in txArguments:
          if isinstance(x, str):
            sOutput += x;
        sPadding = dxArguments.get("sPadding");
        if sPadding:
          sOutput.ljust(120, sPadding);
        oConsoleLock.acquire();
        print(sOutput);
        sys.stdout.flush();
        oConsoleLock.release();
      @staticmethod
      def fStatus(*txArguments, **dxArguments):
        pass;
  
  import sys, urllib.request, urllib.parse, urllib.error;
  from mHTTPClient import cHTTPClient;
  from mFileSystemItem import cFileSystemItem;
  from mTreeServer import cTreeServer, cTreeNode;
  from mMultiThreading import cThread;
  
  bQuick = False;
  bFull = False;
  for sArgument in sys.argv[1:]:
    if sArgument == "--quick": 
      bQuick = True;
    elif sArgument == "--full": 
      bFull = True;
    elif sArgument == "--debug":
      assert m0DebugOutput, \
          "The 'mDebugOutput' module is required to show debug output.";
      import mTreeServer;
      m0DebugOutput.fEnableDebugOutputForModule(mTreeServer);
      import mHTTPServer, mHTTPProtocol, mHTTPConnection, mTCPIPConnection;
      m0DebugOutput.fEnableDebugOutputForModule(mHTTPServer);
      m0DebugOutput.fEnableDebugOutputForModule(mHTTPConnection);
      m0DebugOutput.fEnableDebugOutputForModule(mTCPIPConnection);
      # Having everything from mHTTPProtocol output debug messages may be a bit too verbose, so
      # I've disabled output from the HTTP header classes to keep it reasonably clean.
      # m0DebugOutput.fEnableDebugOutputForClass(mHTTPProtocol.cHTTPHeader);
      # m0DebugOutput.fEnableDebugOutputForClass(mHTTPProtocol.cHTTPHeaders);
      m0DebugOutput.fEnableDebugOutputForClass(mHTTPProtocol.cHTTPRequest);
      m0DebugOutput.fEnableDebugOutputForClass(mHTTPProtocol.cHTTPResponse);
      m0DebugOutput.fEnableDebugOutputForClass(mHTTPProtocol.iHTTPMessage);
      if m0SSL is not None:
        m0DebugOutput.fEnableDebugOutputForModule(m0SSL);
    else:
      raise AssertionError("Unknown argument %s" % sArgument);
  assert not bQuick or not bFull, \
      "Cannot test both quick and full!";
  
  oTreeServer = cTreeServer("Test server");
  
  oChildNode1 = oTreeServer.foCreateChild("First child (html)", "html", "Test <b>html</b>");
  oChildNode1_1 = oChildNode1.foCreateChild("First grantchild");
  oChildNode1_2 = oChildNode1.foCreateChild("Second grantchild (link target)", "text", "Text text");
  
  oChildNode2 = oTreeServer.foCreateChild("Second child (markdown)", "markdown", "Test **markdown**");
  oChildNode3 = oTreeServer.foCreateChild("Third child (link to site)", "url-link", "https://example.com");
  
  oChildNode4 = oTreeServer.foCreateChild("Fourth child (link to Second grantchild)").fLinkToNode(oChildNode1_2);
  
  oTreeServer.fMakeStatic();
  print("Server running @ %s" % oTreeServer.oURL);
  urllib.request.urlopen(str("http://example.com"));
  oClient = cHTTPClient();
  for oURL in [
    oTreeServer.oURL,
    oTreeServer.oURL.foClone(sb0zPath = b"/dxTreeData.json"),
    oTreeServer.oURL.foClone(sb0zPath = b"/stop"),
  ]:
    print("Loading page %s" % oURL);
    oResponse = oClient.fo0GetResponseForURL(oURL);
    assert oResponse and oResponse.uStatusCode == 200, \
        "Unexpected response:\n%s" % repr(oResponse.fsbSerialize());
  print("Waiting for server to stop...");
  oTreeServer.fWait();
  print("Done.");
except Exception as oException:
  if m0DebugOutput:
    m0DebugOutput.fTerminateWithException(oException, guExitCodeInternalError, bShowStacksForAllThread = True);
  raise;
