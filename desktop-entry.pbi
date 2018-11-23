EnableExplicit

Structure DesktopEntry
  filename.s
  name.s
  type.s
  exec.s
  path.s
  icon.s
  noDisplay.b
  hidden.b
  onlyShowIn.s
  notShowIn.s
EndStructure

Procedure ReadDesktopFile(filename.s, *entry.DesktopEntry)
  If OpenPreferences(filename)
    PreferenceGroup("Desktop Entry")
    
    *entry\filename = filename
    *entry\name = ReadPreferenceString("Name", "")
    *entry\type = ReadPreferenceString("Type", "Application")
    *entry\exec = ReadPreferenceString("Exec", "")
    *entry\path = ReadPreferenceString("Path", "")
    *entry\icon = ReadPreferenceString("Icon", "")
    *entry\noDisplay = StrToBool(ReadPreferenceString("NoDisplay", "false"))
    *entry\hidden = StrToBool(ReadPreferenceString("Hidden", "false"))
    *entry\onlyShowIn = ReadPreferenceString("OnlyShowIn", "")
    *entry\notShowIn = ReadPreferenceString("NotShowIn", "")
    
    ClosePreferences()
  EndIf
EndProcedure

Procedure LoadApplicationDesktopFiles(path.s, List entries.DesktopEntry())
  Protected xdgCurrentDesktop.s = GetEnvironmentVariable("XDG_CURRENT_DESKTOP")
  
  Protected dir = ExamineDirectory(#PB_Any, path, "*.desktop")
  If IsDirectory(dir)
    While NextDirectoryEntry(dir)
      If DirectoryEntryType(dir) = #PB_DirectoryEntry_File
        Protected entry.DesktopEntry
        
        ReadDesktopFile(path + "/" + DirectoryEntryName(dir), entry)
        
        If entry\type = "Application" And entry\exec And Not entry\noDisplay And Not entry\hidden
          Protected add.b = #True
          
          If entry\onlyShowIn And Not IsStringFieldInStringField(entry\onlyShowIn, xdgCurrentDesktop, ";", ":")
            add = #False
          EndIf
          
          If entry\notShowIn And IsStringFieldInStringField(entry\notShowIn, xdgCurrentDesktop, ";", ":")
            add = #False
          EndIf
          
          If add
            AddElement(entries())
            entries() = entry
          EndIf
        EndIf
      EndIf
    Wend
    FinishDirectory(dir)
  EndIf
EndProcedure