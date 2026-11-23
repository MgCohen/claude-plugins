# Press a button on a top-level dialog window of one process.
# Usage: answer-dialog.ps1 -ProcessId <pid> [-Title <text>] [-Button <label>] [-List]
param([Parameter(Mandatory)][uint32]$ProcessId, [string]$Title = "", [string]$Button = "", [switch]$List)
Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices; using System.Collections.Generic;
public static class Dlg {
  public delegate bool P(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumWindows(P p, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumChildWindows(IntPtr w, P p, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint p);
  [DllImport("user32.dll")] static extern IntPtr SendMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  static string T(IntPtr h){ var s=new StringBuilder(512); GetWindowText(h,s,512); return s.ToString(); }
  static string C(IntPtr h){ var s=new StringBuilder(256); GetClassName(h,s,256); return s.ToString(); }
  // Dialog windows (class #32770) of the process, with their button labels.
  public static List<KeyValuePair<IntPtr,string>> Dialogs(uint pid){
    var r=new List<KeyValuePair<IntPtr,string>>();
    EnumWindows((h,l)=>{ uint p; GetWindowThreadProcessId(h,out p);
      if(p==pid && IsWindowVisible(h) && C(h)=="#32770") r.Add(new KeyValuePair<IntPtr,string>(h,T(h))); return true;}, IntPtr.Zero);
    return r; }
  public static List<KeyValuePair<IntPtr,string>> Buttons(IntPtr dlg){
    var r=new List<KeyValuePair<IntPtr,string>>();
    EnumChildWindows(dlg,(h,l)=>{ if(C(h)=="Button") r.Add(new KeyValuePair<IntPtr,string>(h,T(h).Replace("&",""))); return true;}, IntPtr.Zero);
    return r; }
  public static void Click(IntPtr b){ SendMessage(b, 0x00F5 /*BM_CLICK*/, IntPtr.Zero, IntPtr.Zero); }
}
"@
$found = [Dlg]::Dialogs($ProcessId) | Where-Object { $Title -eq "" -or $_.Value -eq $Title }
if (-not $found) { Write-Output "no dialog"; exit 3 }
foreach ($d in $found) {
  $btns = [Dlg]::Buttons($d.Key)
  Write-Output ("dialog '{0}' buttons: {1}" -f $d.Value, (($btns | ForEach-Object { $_.Value }) -join ", "))
  if ($List) { continue }
  $b = $btns | Where-Object { $_.Value -ieq $Button } | Select-Object -First 1
  if (-not $b) { Write-Output "no button '$Button'"; exit 4 }
  [Dlg]::Click($b.Key); Write-Output "pressed '$($b.Value)'"; exit 0
}
