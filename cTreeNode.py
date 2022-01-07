import os;

try: # mDebugOutput use is Optional
  from mDebugOutput import ShowDebugOutput, fShowDebugOutput;
except ModuleNotFoundError as oException:
  if oException.args[0] != "No module named 'mDebugOutput'":
    raise;
  ShowDebugOutput = fShowDebugOutput = lambda x: x; # NOP

from mFileSystemItem import cFileSystemItem;
import mHTTPProtocol;
from mNotProvided import *;

def gfCheckIfIdIsUsedInTreeForNode(sId, oRootNode, oNode):
  oExistingNodeWithId = oRootNode.foGetNodeById(sId)
  assert oExistingNodeWithId is None, \
      "%s cannot have id %s because it is already used in the tree by %s" % (oNode.sName, sId, oExistingNodeWithId.sName);

goIconsFolder = cFileSystemItem(__file__).oParent.foGetChild("icons").foMustBeFolder();

class cTreeNode(object):
  sNamespace = "cTreeNode";
  oIconsFolder = goIconsFolder;
  
  def __init__(oSelf, sName, sType = None, xData = None, sId = None, oIconFile = None, sIconURL = None, bOpened = None, bDisabled = None, bSelected = None, sToolTip = None):
    oSelf.sName = sName;
    oSelf.sType = sType; # Valid values: None, "text", "html", "markdown", "node-link", "url-link", "iframe", "img".
    oSelf.xData = xData;
    oSelf.__sId = sId;
    oSelf.oIconFile = oIconFile;
    oSelf.sIconURL = sIconURL;
    oSelf.bOpened = bOpened;
    oSelf.bDisabled = bDisabled;
    oSelf.bSelected = bSelected;
    oSelf.sToolTip = sToolTip;
    oSelf.__oParent = None;
    oSelf.__aoChildren = [];
  
  def foCreateChild(oSelf, sName, *txAdditionalArguments, **dxAdditionalArguments):
    oChild = cTreeNode(sName, *txAdditionalArguments, **dxAdditionalArguments);
    oSelf.fAppendChild(oChild);
    return oChild;
  
  @property
  def sId(oSelf):
    if oSelf.__sId:
      return oSelf.__sId;
    if oSelf.__oParent:
      return "%s>anonymous #%d" % (oSelf.__oParent.sId, oSelf.__oParent.__aoChildren.index(oSelf));
    return "##Anonymous root##";
  
  @sId.setter
  def sId(oSelf, sId):
    assert oSelf.__sId is None, \
        "%s already has an id" % oSelf.sName;
    gfCheckIfIdIsUsedInTreeForNode(sId, oSelf.oRoot, oSelf);
    oSelf.__sId = sId;
  
  def fLinkToNode(oSelf, oTargetTreeNode):
    fAssertType("oTargetTreeNode", oTargetTreeNode, cTreeNode);
    # Make sure oTargetTreeNode is part of the same tree as oSelf.
    assert oSelf.oRoot is oTargetTreeNode.oRoot, \
        "Cannot link to a node that is not part of the same tree!";
    oSelf.sType = "node-link";
    oSelf.xData = oTargetTreeNode;
  
  def fLinkToNodeId(oSelf, sTargetId):
    fAssertType("sTargetId", sTargetId, str);
    oSelf.sType = "node-link";
    oSelf.xData = sTargetId;
  
  def fLinkToURL(oSelf, xURL):
    fAssertType("xURL", xURL, mHTTPProtocol.cURL, str, bytes);
    oSelf.sType = "url-link";
    oSelf.xData = (
      str(xURL.sbAbsolute, "ascii", "strict") if isinstance(xURL, mHTTPProtocol.cURL) else \
      str(xURL, "ascii", "strict") if isinstance(xURL, bytes) else \
      xURL
    );
    assert oSelf.xData, \
        "Invalid URL: %s" % repr(xURL);
  
  def foGetNodeById(oSelf, sId):
    if oSelf.sId == sId: return oSelf;
    for oChild in oSelf.__aoChildren:
      oNode = oChild.foGetNodeById(sId);
      if oNode: return oNode;
    return None;
  
  @property
  def oParent(oSelf):
    return oSelf.__oParent;
  
  @property
  def oRoot(oSelf):
    # Ascend to the root node.
    oNodeInChainToRoot = oSelf;
    while oNodeInChainToRoot.oParent:
      oNodeInChainToRoot = oNodeInChainToRoot.oParent;
    return oNodeInChainToRoot;
  
  @property
  def aoChildren(oSelf):
    return oSelf.__aoChildren[:];
  
  @property
  def aoDescendants(oSelf):
    return oSelf.faoGetDescendantsWithCallback();
  
  def faoGetDescendantsWithCallback(oSelf, fCallback = None):
    aoDescendants = [];
    for oChild in oSelf.__aoChildren:
      fCallback and fCallback(oChild);
      aoDescendants.append(oChild);
      aoDescendants.extend(oChild.faoGetDescendantsWithCallback(fCallback));
    return aoDescendants;
  
  def fRemoveChild(oSelf, oChild):
    assert oChild in oSelf.__aoChildren, \
        "%s is not a child of %s" % (oChild.sName, oSelf.sName);
    oSelf.__aoChildren.remove(oChild);
    oChild.__oParent = None;
  
  def fRemoveChildren(oSelf):
    while oSelf.__aoChildren:
      oSelf.__aoChildren.pop().__oParent = None;
  
  def fRemove(oSelf):
    oParent = oSelf.oParent;
    assert oParent, \
        "%s does not have a parent" % oSelf.sName;
    oParent.fRemoveChild(oSelf);
  
  def fAppendChild(oSelf, oChild):
    assert oChild.oParent is None, \
        "%s already has a parent" % oSelf.sName;
    gfCheckIfIdIsUsedInTreeForNode(oChild.__sId, oSelf.oRoot, oChild);
    oSelf.__aoChildren.append(oChild);
    oChild.__oParent = oSelf;
  
  def fDiscardUserState(oSelf):
    oSelf.bOpened = None;
    oSelf.bSelected = None;
    for oChild in oSelf.__aoChildren:
      oChild.fDiscardUserState();
  
  def fdxGetJSON(oSelf):
    dxJSON = {"text": oSelf.sName};
    bForceDisabled = False;
    asRemarks = [];
    if oSelf.sType:
      if oSelf.sType == "node-link":
        oTargetNode = oSelf.oRoot.foGetNodeById(oSelf.xData) if isinstance(oSelf.xData, str) \
            else oSelf.xData if isinstance(oSelf.xData, cTreeNode) \
            else None;
        if not oTargetNode or (oSelf.oRoot is not oTargetNode.oRoot):
          asRemarks.append("Broken link to %s %s" %("external node" if oTargetNode else "unknown node", repr(oSelf.xData)));
          bForceDisabled = True;
          dxJSON["data"] = {
            "sType": oSelf.sType,
          };
        else:
          asRemarks.append("Link to " + repr(oTargetNode.sName));
          dxJSON["data"] = {
            "sType": oSelf.sType,
            "sData": oTargetNode.sId,
          };
      else:
        dxJSON["data"] = {
          "sType": oSelf.sType,
          "sData": oSelf.xData,
        };
    dxJSON["id"] = oSelf.sId;
    if oSelf.sIconURL is not None:
      dxJSON["icon"] = oSelf.sIconURL;
    elif oSelf.oIconFile is not None:
      dxJSON["icon"] = "icons/%s/%s" % (oSelf.sNamespace, oSelf.oIconFile.sName);
    if oSelf.__aoChildren:
      dxJSON["children"] = [oChild.fdxGetJSON() for oChild in oSelf.__aoChildren];
    dxStateJSON = {};
    if oSelf.bOpened is not None:
      dxStateJSON["opened"] = oSelf.bOpened;
    if bForceDisabled:
      dxStateJSON["disabled"] = True;
    elif oSelf.bDisabled is not None:
      dxStateJSON["disabled"] = oSelf.bDisabled;
    if oSelf.bSelected is not None:
      dxStateJSON["selected"] = oSelf.bSelected;
    if len(dxStateJSON) != 0:
      dxJSON["state"] = dxStateJSON;
    if oSelf.sToolTip:
      asRemarks.insert(0, oSelf.sToolTip);
    if asRemarks:
      dxJSON.setdefault("a_attr", {})["title"] = "\n".join(asRemarks);
    return dxJSON;
