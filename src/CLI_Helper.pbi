;;===============================================================================
;; Module:      CLI_Helper.pbi
;; Version:     1,0
;; Date:        03.02.2010
;; Author:      Michael 'neotoma' Taupitz
;; TargetOS:    ALL.(i hope so...)
;; Compiler:    PureBasic >=4.4 for Windows.
;;
;; Licence:     Do as you wish with it! No warranties either implied
;;              or given... blah blah! :)
;;
;; Description
;; 
;; CLI-Helper makes the using of the Commandline-Interface much easier.
;; Instead of  walking through each parameter in your code, you can define
;; which parameters are wanted, also if they are has arguments.
;; 
;; Example:
;;
;; At first we define the wanted parameters. We have two 'names' per paremeter, a
;; ahort one r.g. 'm' was and a longer 'mode'. We can say if we expect a argument
;; and priovide a small descripetion.
;; You see, this looks much cleaner in your code:
;;
;; CLI_AddOption("m"  ,"mode"    ,#True ,"encode|decode" ,"Switch to a encoding or decoding mode")
;; CLI_AddOption("if" ,"infile"  ,#True ,"filename"      ,"Sourcefile to en/decode")
;; CLI_AddOption("of" ,"outfile" ,#True ,"filename"      ,"Destinationfile (will be overwritten)")  
;; CLI_AddOption("k"  ,"key"     ,#True ,"encryption key","Key for en/decryption")  
;; CLI_AddOption("h"  ,"help"    ,#False ,""             ,"Prints out this usage")
;; CLI_AddOption("V"  ,"version" ,#False ,""             ,"Prints out version details.")
;;
;; Next we do the scanning:
;;  CLI_ScanCommandline()
;;
;; Now we can ask if a parameter was found and do whatever we need to do.
;; ;Print Usage  
;; If CLI_HasOption("h")
;;   CLI_Usage()
;; EndIf
;;
;; The CLI_Usage is also very helpfull - it prints the possible Parameter with ther description.
;; We have also everything stored nicely in the first functions.
;;
;; 
;; The short parameter wants a '-' (-m or -h) the longer '--' (--mode or --help).
;;
;;
;; Changes / History
;;===============================================================================

CompilerIf #PB_Compiler_Version >= 440


;; - Define the information of each entry.
Structure sCliOption
  opt.s           ; short name
  longOpt.s       ; long name
  hasArgs.i       ; bool if Argument wanted
  argName.s       ; name of the argument (for usage)
  optDescription.s; description of the parameter
  optAvailable.i  ; is option available
  optValue.s      ; value of the argument
  required.i      ; bool to remember required parameters
  foundcount.i    ; count how often a option was found
EndStructure

;Here we Store the definitions
NewMap  mapOptions.sCliOption()
;Here we store the found options
NewList llOptions.sCliOption()
;This is our Error-Output.
Define CLI_ERROR_STRING.s

;; -----------------------------------------------------------------------------
;; - CLI_AddOption(opt.s, longOpt.s, hasArgs.i, argName.s, optDescription.s)
;; -----------------------------------------------------------------------------
;; - Description:
;; -  Add a allowed option to the CLI.
;; - 
;; - Parameters:
;; -  opt.s            - Short Option-Name ("m")
;; -  longOpt.s        - Long Option-Name ("mode")
;; -  hasArgs.i        - Boolean. If #True, the next entry is catched as argument
;; -  argName.s        - Name of the Argument for usage-output. ("filename")
;; -  optDescription.s - Description of the Option. Used for Usage.
;; - 
;; -----------------------------------------------------------------------------
;; - Returns: Nothing
;; - 
;;
Procedure CLI_AddOption(opt.s, longOpt.s, hasArgs.i, argName.s, optDescription.s)
  Shared mapOptions()
  mapOptions(opt)\opt = opt
  mapOptions(opt)\longOpt = longOpt
  mapOptions(opt)\hasArgs = hasArgs
  mapOptions(opt)\argName = argName
  mapOptions(opt)\optDescription = optDescription
  mapOptions(opt)\optAvailable = #False
  mapOptions(opt)\foundcount = 0
EndProcedure


;; -----------------------------------------------------------------------------
;; - CLI_ScanComandline()
;; -----------------------------------------------------------------------------
;; - Description:
;; -   Scans the Commandline. Make Sure you defined the possible options before.
;; - 
;; - Parameters:
;; - 
;; -----------------------------------------------------------------------------
;; - Returns: Nothing
;; - 
;;
Procedure CLI_ScanCommandline()
  Shared mapOptions(), llOptions()

  Protected pcount.i = CountProgramParameters()
  Protected param.s
  Protected i.i = 0
  
  While i < pcount
    param = ProgramParameter(i)
    ForEach mapOptions()
      If param = "-"+mapOptions()\opt Or  param= "--"+mapOptions()\longOpt
        AddElement( llOptions() )
        llOptions()\opt = mapOptions()\opt
        llOptions()\longOpt= mapOptions()\longOpt
        llOptions()\hasArgs= mapOptions()\hasArgs
        llOptions()\optDescription= mapOptions()\optDescription
        llOptions()\optAvailable = #True       
        mapOptions()\foundcount + 1 
        If mapOptions()\hasArgs
          i+1          
          llOptions()\optValue = ProgramParameter(i)
        EndIf
      EndIf
    Next
    
    i+1
  Wend
EndProcedure

;; -----------------------------------------------------------------------------
;; - CLI_HasOption(opt.s)
;; -----------------------------------------------------------------------------
;; - Description:
;; -   Checks if the option (opt.s) was found on the commandline
;; - 
;; - Parameters:
;; -    opt.s  - Short name of the option
;; -----------------------------------------------------------------------------
;; - Returns: #True if the Options was found, otherwise #False
;; - 
;;
Procedure.i CLI_HasOption(opt.s)
  Shared llOptions()
  Protected RetVal.i = #False
  ForEach  llOptions()  
    If llOptions()\opt = opt Or llOptions()\longOpt = opt
      RetVal = #True
      Break
    EndIf
  Next
  ProcedureReturn RetVal
EndProcedure  

;; -----------------------------------------------------------------------------
;; - CLI_GetOptionValue(opt.s)
;; -----------------------------------------------------------------------------
;; - Description:
;; -   Returns the argument of the option (opt.s).
;; - 
;; - Parameters:
;; -    opt.s  - Short name of the option
;; -----------------------------------------------------------------------------
;; - Returns: Argument of the Option
;; - 
;;
Procedure.s CLI_GetOptionValue(opt.s)
  Shared llOptions()
  ForEach  llOptions()  
    If llOptions()\opt = opt Or llOptions()\longOpt = opt
      ProcedureReturn llOptions()\optValue
    EndIf
  Next
  ProcedureReturn ""
EndProcedure  
         
;; -----------------------------------------------------------------------------
;; - CLI_SetRequired(opt.s, bReq.i = #True)  
;; -----------------------------------------------------------------------------
;; - Description:
;; -   Set the option (opt) to required.
;; - 
;; - Parameters:
;; -    opt.s  - Short name of the option
;; -    bReq.i - (optional) the Falg. if #True the Option is marked as required.
;; -----------------------------------------------------------------------------
;; - Returns: Nothing
;; - 
;;
Procedure CLI_SetRequired(opt.s, bReq.i = #True)  
  Shared mapOptions()
  If FindMapElement(mapOptions(),opt)
    mapOptions(opt)\required = bReq
  EndIf
EndProcedure

;; -----------------------------------------------------------------------------
;; - CLI_isRequired(opt.s)  
;; -----------------------------------------------------------------------------
;; - Description:
;; -   Checks if a option was required
;; - 
;; - Parameters:
;; -    opt.s  - Short name of the option
;; -----------------------------------------------------------------------------
;; - Returns: Required-Flag
;; - 
;;
Procedure CLI_isRequired(opt.s)  
  Shared mapOptions()
  ProcedureReturn mapOptions(opt)\required 
EndProcedure


;; -----------------------------------------------------------------------------
;; - CLI_CheckRequired()  
;; -----------------------------------------------------------------------------
;; - Description:
;; -   Checks if a required option was missing.
;; -   For each missed option it prompts a Info to the Commandline.
;; - 
;; -----------------------------------------------------------------------------
;; - Returns: #False if one or more required options missed
;; - 
;;
Procedure.i CLI_CheckRequired()  
  Shared mapOptions()
  Protected  retVal = #True
    
  ForEach mapOptions()
    If mapOptions()\required And mapOptions()\foundcount = 0
      Print("-"+mapOptions()\opt)
      If mapOptions()\hasArgs
        Print(" <"+mapOptions()\argName+">")
      EndIf
      Print(" is Missing!")
      PrintN("")
      retVal = #False 
    EndIf
  Next
  ProcedureReturn RetVal
EndProcedure

      
;; -----------------------------------------------------------------------------
;; - CLI_Usage()
;; -----------------------------------------------------------------------------
;; - Description:
;; -   Prints a Usage-Information to the Commandline.
;; -   The output is based on the defined Options.
;; - 
;; - Parameters:
;; -----------------------------------------------------------------------------
;; - Returns: Nothing
;; - 
;;
Procedure CLI_Usage()
  Shared mapOptions()
  Protected strTemp.s = "usage:"
  
  ForEach mapOptions()
    If mapOptions()\hasArgs
      strTemp +" [-"+mapOptions()\opt+" <"+mapOptions()\argName+">]"
    Else
      strTemp +" [-"+mapOptions()\opt+"]"
    EndIf 
  Next
  PrintN(strTemp)
  
  ForEach mapOptions()
    strTemp = " -"+mapOptions()\opt+",--"+mapOptions()\longOpt
    If mapOptions()\hasArgs
      strTemp+" <"+mapOptions()\argName+">"
    EndIf
    
    PrintN( LSet(strTemp, 40, " ") + mapOptions()\optDescription )
  Next          

EndProcedure  

;; -----------------------------------------------------------------------------
;; - CLI_HelpPrinter(Header.s, Footer.s)
;; -----------------------------------------------------------------------------
;; - Description:
;; -   Prints the Header, the Usage and Footer
;; - 
;; - Parameters:
;; -----------------------------------------------------------------------------
;; - Returns: Nothing
;; - 
;;
Procedure CLI_HelpPrinter(Header.s, Footer.s)
  PrintN(Header)
  PrintN(RSet("",Len(Header),"-"))
  PrintN("")
  CLI_Usage()
  PrintN(Footer)
  PrintN("")
EndProcedure  

CompilerElse
  CompilerError "CLI_Helper needs PureBasic 4.40 or greater. (Maps)"
CompilerEndIf
