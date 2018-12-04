EnableExplicit

Enumeration
  #File_InputDevice
EndEnumeration

Enumeration
  #SIGHUP = 1
  #SIGINT
  #SIGQUIT
  #SIGILL
  #SIGTRAP
  #SIGABRT
  #SIGBUS
  #SIGFPE
  #SIGKILL
  #SIGUSR1
  #SIGSEGV
  #SIGUSR2
  #SIGPIPE
  #SIGALRM
  #SIGTERM
  #SIGSTKFLT
  #SIGCHLD
  #SIGCONT
  #SIGSTOP
  #SIGTSTP
  #SIGTTIN
  #SIGTTOU
  #SIGURG
  #SIGXCPU
  #SIGXFSZ
  #SIGVTALRM
  #SIGPROF
  #SIGWINCH
  #SIGPOLL
  #SIGPWR
  #SIGSYS
EndEnumeration

Enumeration
  #ActionHandling_None
  #ActionHandling_LockKeys
  #ActionHandling_All
EndEnumeration

Structure Shortcut
  name.s
  action.s
  actionData.s
EndStructure

Structure Config
  keyboardInputDevice.s
  icons.s
  useTrayIcon.b
EndStructure

Structure InputEvent
  timestamp.b[16]
  type.w
  code.w
  value.b[4]
EndStructure

;- Actions
#Action_LaunchApplication = "launchApplication"
#Action_ExecuteCommand = "executeCommand"
#Action_OpenFolder = "openFolder"
#Action_InputText = "inputText"
#Action_InputKeySequence = "inputKeySequence"
#Action_LockKeys = "lockKeys"

Global NewMap shortcuts.Shortcut()
Global NewList applicationList.DesktopEntry()
Global config.Config
Global configDir.s
Global configFile.s
Global shortcutsFile.s
Global inputEventListenerThread
Global allowActionHandling = #ActionHandling_All
Global appPath.s = GetPathPart(ProgramFilename())

; Temporary (test) executable is created in "src" directory
CompilerIf Not #PB_Editor_CreateExecutable
  appPath = GetPathPart(RTrim(appPath, "/"))
CompilerEndIf

Procedure.b StrToBool(string.s)
  Select LCase(string)
    Case "true"
      ProcedureReturn #True
    Case "false"
      ProcedureReturn #False
    Default
      ProcedureReturn #Null
  EndSelect
EndProcedure

Procedure.s BoolToStr(boolean.b)
  If boolean
    ProcedureReturn "true"
  Else
    ProcedureReturn "false"
  EndIf
EndProcedure

Procedure.s StringToUtf8(string.s)
  Protected *memory
  Protected utf8String.s
  
  *memory = AllocateMemory(StringByteLength(string, #PB_Unicode) + 2)
  PokeS(*memory, string, -1,  #PB_UTF8)
  utf8String = PeekS(*memory)
  FreeMemory(*memory)
  
  ProcedureReturn utf8String
EndProcedure

Procedure.b IsStringFieldInStringField(string1.s, string2.s, separator1.s, separator2.s)
  Protected index1
  Protected index2
  
  For index1 = 0 To CountString(string1, separator1)
    Protected field1.s = StringField(string1, index1 + 1, separator1)
    
    For index2 = 0 To CountString(string2, separator2)
      If field1 = StringField(string2, index2 + 1, separator2)
        ProcedureReturn #True
      EndIf
    Next
  Next
  
  ProcedureReturn #False
EndProcedure

Procedure LoadConfig()
  If OpenPreferences(configFile)
    config\keyboardInputDevice = ReadPreferenceString("keyboard-input-device", "")
    config\icons = ReadPreferenceString("icons", "dark")
    config\useTrayIcon = StrToBool(ReadPreferenceString("use-tray-icon", "true"))
    ClosePreferences()
  EndIf
EndProcedure

Procedure SaveConfig()
  If CreatePreferences(configFile)
    WritePreferenceString("keyboard-input-device", config\keyboardInputDevice)
    WritePreferenceString("icons", config\icons)
    WritePreferenceString("use-tray-icon", BoolToStr(config\useTrayIcon))
    ClosePreferences()
  EndIf
EndProcedure

Procedure LoadShortcutsFromFile()
  ClearMap(shortcuts())
  
  If OpenPreferences(shortcutsFile)
    ExaminePreferenceGroups()
    While NextPreferenceGroup()
      Protected keyString.s = PreferenceGroupName()
      
      shortcuts(keyString)\name = ReadPreferenceString("name", "")
      shortcuts(keyString)\action = ReadPreferenceString("action", "")
      shortcuts(keyString)\actionData = ReadPreferenceString("data", "")
    Wend
    
    ClosePreferences()
  EndIf
EndProcedure

Procedure SaveShortcutsToFile()
  If CreatePreferences(shortcutsFile, #PB_Preference_GroupSeparator)
    ForEach shortcuts()
      PreferenceGroup(MapKey(shortcuts()))
      
      WritePreferenceString("name", shortcuts()\name)
      WritePreferenceString("action", shortcuts()\action)
      WritePreferenceString("data", shortcuts()\actionData)
    Next
    
    ClosePreferences()
  EndIf
EndProcedure

Procedure.b Invert(boolean.b)
  If boolean
    ProcedureReturn #False
  Else
    ProcedureReturn #True
  EndIf
EndProcedure

Procedure RunStandardProgram(filename.s, workingDirectory.s, flags = 0, senderProgram = 0)
  Protected result
  
  result = RunProgram("xdg-open", filename, workingDirectory, flags, senderProgram)
  If result
    ProcedureReturn result
  EndIf
  
  ProcedureReturn RunProgram("gnome-open", filename, workingDirectory, flags, senderProgram)
EndProcedure

Procedure.s ActionToString(action.s)
  Select action
    Case #Action_LaunchApplication
      ProcedureReturn "Launch application"
    Case #Action_ExecuteCommand
      ProcedureReturn "Execute command"
    Case #Action_OpenFolder
      ProcedureReturn "Open folder"
    Case #Action_InputText
      ProcedureReturn "Input text"
    Case #Action_InputKeySequence
      ProcedureReturn "Input key sequence"
    Case #Action_LockKeys
      ProcedureReturn "Lock keys"
  EndSelect
EndProcedure

Procedure.b IsPIDRunning(pid)
  ; Sending signal 0 to the PID results in just reporting the running state (0 = running, -1 = error/not running)
  If kill_(pid, 0)
    ProcedureReturn #False
  Else
    ProcedureReturn #True
  EndIf
EndProcedure

Procedure RequireSingleInstance()
  Protected ownPID = getpid_()
  Protected file = OpenFile(#PB_Any, configDir + "/app.pid")
  If IsFile(file)
    Protected pid = Val(ReadString(file))
    If pid
      If pid <> ownPID And IsPIDRunning(pid)
        CloseFile(file)
        ProcedureReturn pid
      EndIf
    EndIf
    FileSeek(file, 0)
    TruncateFile(file)
    WriteString(file, Str(ownPID))
    CloseFile(file)
    ProcedureReturn 0
  EndIf
  ProcedureReturn -1
EndProcedure
