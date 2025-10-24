Scenario 1

Test 1

DEBUG: Updating folder from 'AI' to 'AI_TEST'
DEBUG: Entry object id: 2217015716672
DEBUG: Entry before update: {'allowEmpty': False, 'entries': [{'icon': None, 'profile': '{564d9267-5564-42a2-b951-4bf1480a0e8e}', 'type': 'profile'}, {'icon': None, 'profile': '{e356a276-13f1-4a2e-bbc5-b9df9d40a14a}', 'type': 'profile'}, {'icon': None, 'profile': '{d9a270a3-164e-4df2-9f9b-4d84d33d12cd}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{00517e18-8a5f-4a31-a793-281732c42cef}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{a61330fd-917f-4fa3-a976-df0dafb7108a}', 'type': 'profile'}, {'icon': None, 'profile': '{a33cac7d-752a-4102-948c-7099b88b6bf3}', 'type': 'profile'}, {'icon': None, 'profile': '{b3ddffda-cea2-4461-b620-b4f454ab10cf}', 'type': 'profile'}, {'icon': None, 'profile': '{62ba5af3-9f7b-4526-b6fd-1498f350dd35}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{0d1da92f-d1ec-4b4b-a50b-2946d5195a55}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{b8a43965-b235-46ae-9124-743aa3b21088}', 'type': 'profile'}, {'icon': None, 'profile': '{df1d8588-7e23-47d3-9167-5abab0718af6}', 'type': 'profile'}], 'icon': 'Y:\\images\\icons\\ai_1.png', 'inline': 'never', 'name': 'AI', 'type': 'folder'}
DEBUG: Entry after update: {'allowEmpty': False, 'entries': [{'icon': None, 'profile': '{564d9267-5564-42a2-b951-4bf1480a0e8e}', 'type': 'profile'}, {'icon': None, 'profile': '{e356a276-13f1-4a2e-bbc5-b9df9d40a14a}', 'type': 'profile'}, {'icon': None, 'profile': '{d9a270a3-164e-4df2-9f9b-4d84d33d12cd}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{00517e18-8a5f-4a31-a793-281732c42cef}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{a61330fd-917f-4fa3-a976-df0dafb7108a}', 'type': 'profile'}, {'icon': None, 'profile': '{a33cac7d-752a-4102-948c-7099b88b6bf3}', 'type': 'profile'}, {'icon': None, 'profile': '{b3ddffda-cea2-4461-b620-b4f454ab10cf}', 'type': 'profile'}, {'icon': None, 'profile': '{62ba5af3-9f7b-4526-b6fd-1498f350dd35}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{0d1da92f-d1ec-4b4b-a50b-2946d5195a55}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{b8a43965-b235-46ae-9124-743aa3b21088}', 'type': 'profile'}, {'icon': None, 'profile': '{df1d8588-7e23-47d3-9167-5abab0718af6}', 'type': 'profile'}], 'icon': 'Y:\\images\\icons\\ai_1.png', 'inline': 'never', 'name': 'AI_TEST', 'type': 'folder'}
DEBUG: WARNING - Entry not found in data_schemes!


Nothing changed in the list

Test 2

DEBUG: Adding profile 'DISM_SFC'
DEBUG: Profile GUID: {4b82abc9-308a-47cd-802e-fb058efba1b8}
DEBUG: Current selection type: folder
DEBUG: Added to folder: AI

profile 'DISM_SFC' did not appear in AI folder in the list. I even saved the changes left the program and checked in wt - no change to folder AI 

Test 3

Inside folder AI i tried to move profile CC_TWEAK with the buttons up and down - nothing happened and no debug messages in the terminal.


  Test 1 - Update Folder Name:
  1. Select the "AI" folder
  2. Change name to "AI_TEST"
  3. Click "Update Item"
  4. Send me the console output starting with "DEBUG:"

  Test 2 - Add Profile to Folder:
  1. Select the "AI" folder (or any folder)
  2. Click "Add Profile"
  3. Select a profile from the list
  4. Send me the console output

  Test 3 - Move Profile Up/Down:
  1. Expand a folder that has profiles
  2. Select a profile inside the folder
  3. Click "Move Up" or "Move Down"
  4. Tell me if it moved
  
  ❯ python wt_manager.pyw
DEBUG loadFolders: Clearing tree and reloading from data_schemes
DEBUG loadFolders: data_schemes has 12 root items
DEBUG loadFolders: Adding item 0: type=folder, name=Powershell
DEBUG addTreeItem: Creating folder item with name='Powershell', entry_id=2300635495872
DEBUG addTreeItem: Folder 'Powershell' has 11 children
DEBUG loadFolders: Adding item 1: type=folder, name=QNAP
DEBUG addTreeItem: Creating folder item with name='QNAP', entry_id=2300635091392
DEBUG addTreeItem: Folder 'QNAP' has 4 children
DEBUG loadFolders: Adding item 2: type=folder, name=AI
DEBUG addTreeItem: Creating folder item with name='AI', entry_id=2300638996096
DEBUG addTreeItem: Folder 'AI' has 15 children
DEBUG loadFolders: Adding item 3: type=folder, name=Backup
DEBUG addTreeItem: Creating folder item with name='Backup', entry_id=2300638998976
DEBUG addTreeItem: Folder 'Backup' has 3 children
DEBUG loadFolders: Adding item 4: type=folder, name=CMD
DEBUG addTreeItem: Creating folder item with name='CMD', entry_id=2300638998720
DEBUG addTreeItem: Folder 'CMD' has 3 children
DEBUG loadFolders: Adding item 5: type=folder, name=Development
DEBUG addTreeItem: Creating folder item with name='Development', entry_id=2300638999360
DEBUG addTreeItem: Folder 'Development' has 13 children
DEBUG loadFolders: Adding item 6: type=folder, name=WSL
DEBUG addTreeItem: Creating folder item with name='WSL', entry_id=2300636853632
DEBUG addTreeItem: Folder 'WSL' has 1 children
DEBUG loadFolders: Adding item 7: type=folder, name=Raspberry
DEBUG addTreeItem: Creating folder item with name='Raspberry', entry_id=2300636851392
DEBUG addTreeItem: Folder 'Raspberry' has 1 children
DEBUG loadFolders: Adding item 8: type=folder, name=Utilities
DEBUG addTreeItem: Creating folder item with name='Utilities', entry_id=2300636853568
DEBUG addTreeItem: Folder 'Utilities' has 5 children
DEBUG loadFolders: Adding item 9: type=separator, name=N/A
DEBUG loadFolders: Adding item 10: type=remainingProfiles, name=N/A
DEBUG loadFolders: Adding item 11: type=folder, name=New Folder
DEBUG addTreeItem: Creating folder item with name='New Folder', entry_id=2300636855872
DEBUG addTreeItem: Folder 'New Folder' has 0 children
DEBUG loadFolders: Tree now has 12 top-level items
DEBUG: Updating folder from 'AI' to 'AI_TEST'
DEBUG: Entry object id: 2300631830912
DEBUG: Entry before update: {'allowEmpty': False, 'entries': [{'icon': None, 'profile': '{564d9267-5564-42a2-b951-4bf1480a0e8e}', 'type': 'profile'}, {'icon': None, 'profile': '{e356a276-13f1-4a2e-bbc5-b9df9d40a14a}', 'type': 'profile'}, {'icon': None, 'profile': '{d9a270a3-164e-4df2-9f9b-4d84d33d12cd}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{00517e18-8a5f-4a31-a793-281732c42cef}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{a61330fd-917f-4fa3-a976-df0dafb7108a}', 'type': 'profile'}, {'icon': None, 'profile': '{a33cac7d-752a-4102-948c-7099b88b6bf3}', 'type': 'profile'}, {'icon': None, 'profile': '{b3ddffda-cea2-4461-b620-b4f454ab10cf}', 'type': 'profile'}, {'icon': None, 'profile': '{62ba5af3-9f7b-4526-b6fd-1498f350dd35}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{0d1da92f-d1ec-4b4b-a50b-2946d5195a55}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{b8a43965-b235-46ae-9124-743aa3b21088}', 'type': 'profile'}, {'icon': None, 'profile': '{df1d8588-7e23-47d3-9167-5abab0718af6}', 'type': 'profile'}], 'icon': 'Y:\\images\\icons\\ai_1.png', 'inline': 'never', 'name': 'AI', 'type': 'folder'}
DEBUG: Entry after update: {'allowEmpty': False, 'entries': [{'icon': None, 'profile': '{564d9267-5564-42a2-b951-4bf1480a0e8e}', 'type': 'profile'}, {'icon': None, 'profile': '{e356a276-13f1-4a2e-bbc5-b9df9d40a14a}', 'type': 'profile'}, {'icon': None, 'profile': '{d9a270a3-164e-4df2-9f9b-4d84d33d12cd}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{00517e18-8a5f-4a31-a793-281732c42cef}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{a61330fd-917f-4fa3-a976-df0dafb7108a}', 'type': 'profile'}, {'icon': None, 'profile': '{a33cac7d-752a-4102-948c-7099b88b6bf3}', 'type': 'profile'}, {'icon': None, 'profile': '{b3ddffda-cea2-4461-b620-b4f454ab10cf}', 'type': 'profile'}, {'icon': None, 'profile': '{62ba5af3-9f7b-4526-b6fd-1498f350dd35}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{0d1da92f-d1ec-4b4b-a50b-2946d5195a55}', 'type': 'profile'}, {'type': 'separator'}, {'icon': None, 'profile': '{b8a43965-b235-46ae-9124-743aa3b21088}', 'type': 'profile'}, {'icon': None, 'profile': '{df1d8588-7e23-47d3-9167-5abab0718af6}', 'type': 'profile'}], 'icon': 'Y:\\images\\icons\\ai_1.png', 'inline': 'never', 'name': 'AI_TEST', 'type': 'folder'}
DEBUG: WARNING - Entry not found in data_schemes!
DEBUG loadFolders: Clearing tree and reloading from data_schemes
DEBUG loadFolders: data_schemes has 12 root items
DEBUG loadFolders: Adding item 0: type=folder, name=Powershell
DEBUG addTreeItem: Creating folder item with name='Powershell', entry_id=2300635495872
DEBUG addTreeItem: Folder 'Powershell' has 11 children
DEBUG loadFolders: Adding item 1: type=folder, name=QNAP
DEBUG addTreeItem: Creating folder item with name='QNAP', entry_id=2300635091392
DEBUG addTreeItem: Folder 'QNAP' has 4 children
DEBUG loadFolders: Adding item 2: type=folder, name=AI
DEBUG addTreeItem: Creating folder item with name='AI', entry_id=2300638996096
DEBUG addTreeItem: Folder 'AI' has 15 children
DEBUG loadFolders: Adding item 3: type=folder, name=Backup
DEBUG addTreeItem: Creating folder item with name='Backup', entry_id=2300638998976
DEBUG addTreeItem: Folder 'Backup' has 3 children
DEBUG loadFolders: Adding item 4: type=folder, name=CMD
DEBUG addTreeItem: Creating folder item with name='CMD', entry_id=2300638998720
DEBUG addTreeItem: Folder 'CMD' has 3 children
DEBUG loadFolders: Adding item 5: type=folder, name=Development
DEBUG addTreeItem: Creating folder item with name='Development', entry_id=2300638999360
DEBUG addTreeItem: Folder 'Development' has 13 children
DEBUG loadFolders: Adding item 6: type=folder, name=WSL
DEBUG addTreeItem: Creating folder item with name='WSL', entry_id=2300636853632
DEBUG addTreeItem: Folder 'WSL' has 1 children
DEBUG loadFolders: Adding item 7: type=folder, name=Raspberry
DEBUG addTreeItem: Creating folder item with name='Raspberry', entry_id=2300636851392
DEBUG addTreeItem: Folder 'Raspberry' has 1 children
DEBUG loadFolders: Adding item 8: type=folder, name=Utilities
DEBUG addTreeItem: Creating folder item with name='Utilities', entry_id=2300636853568
DEBUG addTreeItem: Folder 'Utilities' has 5 children
DEBUG loadFolders: Adding item 9: type=separator, name=N/A
DEBUG loadFolders: Adding item 10: type=remainingProfiles, name=N/A
DEBUG loadFolders: Adding item 11: type=folder, name=New Folder
DEBUG addTreeItem: Creating folder item with name='New Folder', entry_id=2300636855872
DEBUG addTreeItem: Folder 'New Folder' has 0 children
DEBUG loadFolders: Tree now has 12 top-level items
DEBUG: Adding profile 'DISM_SFC'
DEBUG: Profile GUID: {4b82abc9-308a-47cd-802e-fb058efba1b8}
DEBUG: Current selection type: profile
DEBUG: Added to parent folder: AI
DEBUG loadFolders: Clearing tree and reloading from data_schemes
DEBUG loadFolders: data_schemes has 12 root items
DEBUG loadFolders: Adding item 0: type=folder, name=Powershell
DEBUG addTreeItem: Creating folder item with name='Powershell', entry_id=2300635495872
DEBUG addTreeItem: Folder 'Powershell' has 11 children
DEBUG loadFolders: Adding item 1: type=folder, name=QNAP
DEBUG addTreeItem: Creating folder item with name='QNAP', entry_id=2300635091392
DEBUG addTreeItem: Folder 'QNAP' has 4 children
DEBUG loadFolders: Adding item 2: type=folder, name=AI
DEBUG addTreeItem: Creating folder item with name='AI', entry_id=2300638996096
DEBUG addTreeItem: Folder 'AI' has 15 children
DEBUG loadFolders: Adding item 3: type=folder, name=Backup
DEBUG addTreeItem: Creating folder item with name='Backup', entry_id=2300638998976
DEBUG addTreeItem: Folder 'Backup' has 3 children
DEBUG loadFolders: Adding item 4: type=folder, name=CMD
DEBUG addTreeItem: Creating folder item with name='CMD', entry_id=2300638998720
DEBUG addTreeItem: Folder 'CMD' has 3 children
DEBUG loadFolders: Adding item 5: type=folder, name=Development
DEBUG addTreeItem: Creating folder item with name='Development', entry_id=2300638999360
DEBUG addTreeItem: Folder 'Development' has 13 children
DEBUG loadFolders: Adding item 6: type=folder, name=WSL
DEBUG addTreeItem: Creating folder item with name='WSL', entry_id=2300636853632
DEBUG addTreeItem: Folder 'WSL' has 1 children
DEBUG loadFolders: Adding item 7: type=folder, name=Raspberry
DEBUG addTreeItem: Creating folder item with name='Raspberry', entry_id=2300636851392
DEBUG addTreeItem: Folder 'Raspberry' has 1 children
DEBUG loadFolders: Adding item 8: type=folder, name=Utilities
DEBUG addTreeItem: Creating folder item with name='Utilities', entry_id=2300636853568
DEBUG addTreeItem: Folder 'Utilities' has 5 children
DEBUG loadFolders: Adding item 9: type=separator, name=N/A
DEBUG loadFolders: Adding item 10: type=remainingProfiles, name=N/A
DEBUG loadFolders: Adding item 11: type=folder, name=New Folder
DEBUG addTreeItem: Creating folder item with name='New Folder', entry_id=2300636855872
DEBUG addTreeItem: Folder 'New Folder' has 0 children
DEBUG loadFolders: Tree now has 12 top-level items
DEBUG moveFolderItemUp: Function called
DEBUG moveFolderItemUp: Moving profile {62ba5af3-9f7b-4526-b6fd-1498f350dd35}
DEBUG moveFolderItemUp: Item is in a folder
DEBUG moveFolderItemUp: Current index: 9, list length: 15
DEBUG moveFolderItemUp: Moved from 9 to 8
DEBUG moveFolderItemUp: Reloading folders
DEBUG loadFolders: Clearing tree and reloading from data_schemes
DEBUG loadFolders: data_schemes has 12 root items
DEBUG loadFolders: Adding item 0: type=folder, name=Powershell
DEBUG addTreeItem: Creating folder item with name='Powershell', entry_id=2300635495872
DEBUG addTreeItem: Folder 'Powershell' has 11 children
DEBUG loadFolders: Adding item 1: type=folder, name=QNAP
DEBUG addTreeItem: Creating folder item with name='QNAP', entry_id=2300635091392
DEBUG addTreeItem: Folder 'QNAP' has 4 children
DEBUG loadFolders: Adding item 2: type=folder, name=AI
DEBUG addTreeItem: Creating folder item with name='AI', entry_id=2300638996096
DEBUG addTreeItem: Folder 'AI' has 15 children
DEBUG loadFolders: Adding item 3: type=folder, name=Backup
DEBUG addTreeItem: Creating folder item with name='Backup', entry_id=2300638998976
DEBUG addTreeItem: Folder 'Backup' has 3 children
DEBUG loadFolders: Adding item 4: type=folder, name=CMD
DEBUG addTreeItem: Creating folder item with name='CMD', entry_id=2300638998720
DEBUG addTreeItem: Folder 'CMD' has 3 children
DEBUG loadFolders: Adding item 5: type=folder, name=Development
DEBUG addTreeItem: Creating folder item with name='Development', entry_id=2300638999360
DEBUG addTreeItem: Folder 'Development' has 13 children
DEBUG loadFolders: Adding item 6: type=folder, name=WSL
DEBUG addTreeItem: Creating folder item with name='WSL', entry_id=2300636853632
DEBUG addTreeItem: Folder 'WSL' has 1 children
DEBUG loadFolders: Adding item 7: type=folder, name=Raspberry
DEBUG addTreeItem: Creating folder item with name='Raspberry', entry_id=2300636851392
DEBUG addTreeItem: Folder 'Raspberry' has 1 children
DEBUG loadFolders: Adding item 8: type=folder, name=Utilities
DEBUG addTreeItem: Creating folder item with name='Utilities', entry_id=2300636853568
DEBUG addTreeItem: Folder 'Utilities' has 5 children
DEBUG loadFolders: Adding item 9: type=separator, name=N/A
DEBUG loadFolders: Adding item 10: type=remainingProfiles, name=N/A
DEBUG loadFolders: Adding item 11: type=folder, name=New Folder
DEBUG addTreeItem: Creating folder item with name='New Folder', entry_id=2300636855872
DEBUG addTreeItem: Folder 'New Folder' has 0 children
DEBUG loadFolders: Tree now has 12 top-level items
DEBUG loadFolders: Clearing tree and reloading from data_schemes
DEBUG loadFolders: data_schemes has 12 root items
DEBUG loadFolders: Adding item 0: type=folder, name=Powershell
DEBUG addTreeItem: Creating folder item with name='Powershell', entry_id=2300635495872
DEBUG addTreeItem: Folder 'Powershell' has 11 children
DEBUG loadFolders: Adding item 1: type=folder, name=QNAP
DEBUG addTreeItem: Creating folder item with name='QNAP', entry_id=2300635091392
DEBUG addTreeItem: Folder 'QNAP' has 4 children
DEBUG loadFolders: Adding item 2: type=folder, name=AI
DEBUG addTreeItem: Creating folder item with name='AI', entry_id=2300638996096
DEBUG addTreeItem: Folder 'AI' has 15 children
DEBUG loadFolders: Adding item 3: type=folder, name=Backup
DEBUG addTreeItem: Creating folder item with name='Backup', entry_id=2300638998976
DEBUG addTreeItem: Folder 'Backup' has 3 children
DEBUG loadFolders: Adding item 4: type=folder, name=CMD
DEBUG addTreeItem: Creating folder item with name='CMD', entry_id=2300638998720
DEBUG addTreeItem: Folder 'CMD' has 3 children
DEBUG loadFolders: Adding item 5: type=folder, name=Development
DEBUG addTreeItem: Creating folder item with name='Development', entry_id=2300638999360
DEBUG addTreeItem: Folder 'Development' has 13 children
DEBUG loadFolders: Adding item 6: type=folder, name=WSL
DEBUG addTreeItem: Creating folder item with name='WSL', entry_id=2300636853632
DEBUG addTreeItem: Folder 'WSL' has 1 children
DEBUG loadFolders: Adding item 7: type=folder, name=Raspberry
DEBUG addTreeItem: Creating folder item with name='Raspberry', entry_id=2300636851392
DEBUG addTreeItem: Folder 'Raspberry' has 1 children
DEBUG loadFolders: Adding item 8: type=folder, name=Utilities
DEBUG addTreeItem: Creating folder item with name='Utilities', entry_id=2300636853568
DEBUG addTreeItem: Folder 'Utilities' has 5 children
DEBUG loadFolders: Adding item 9: type=separator, name=N/A
DEBUG loadFolders: Adding item 10: type=remainingProfiles, name=N/A
DEBUG loadFolders: Adding item 11: type=folder, name=New Folder
DEBUG addTreeItem: Creating folder item with name='New Folder', entry_id=2300636855872
DEBUG addTreeItem: Folder 'New Folder' has 0 children
DEBUG loadFolders: Tree now has 12 top-level items
DEBUG moveFolderItemUp: Function called
DEBUG moveFolderItemUp: Moving profile {b3ddffda-cea2-4461-b620-b4f454ab10cf}
DEBUG moveFolderItemUp: Item is in a folder
DEBUG moveFolderItemUp: Current index: 8, list length: 15
DEBUG moveFolderItemUp: Moved from 8 to 7
DEBUG moveFolderItemUp: Reloading folders
DEBUG loadFolders: Clearing tree and reloading from data_schemes
DEBUG loadFolders: data_schemes has 12 root items
DEBUG loadFolders: Adding item 0: type=folder, name=Powershell
DEBUG addTreeItem: Creating folder item with name='Powershell', entry_id=2300635495872
DEBUG addTreeItem: Folder 'Powershell' has 11 children
DEBUG loadFolders: Adding item 1: type=folder, name=QNAP
DEBUG addTreeItem: Creating folder item with name='QNAP', entry_id=2300635091392
DEBUG addTreeItem: Folder 'QNAP' has 4 children
DEBUG loadFolders: Adding item 2: type=folder, name=AI
DEBUG addTreeItem: Creating folder item with name='AI', entry_id=2300638996096
DEBUG addTreeItem: Folder 'AI' has 15 children
DEBUG loadFolders: Adding item 3: type=folder, name=Backup
DEBUG addTreeItem: Creating folder item with name='Backup', entry_id=2300638998976
DEBUG addTreeItem: Folder 'Backup' has 3 children
DEBUG loadFolders: Adding item 4: type=folder, name=CMD
DEBUG addTreeItem: Creating folder item with name='CMD', entry_id=2300638998720
DEBUG addTreeItem: Folder 'CMD' has 3 children
DEBUG loadFolders: Adding item 5: type=folder, name=Development
DEBUG addTreeItem: Creating folder item with name='Development', entry_id=2300638999360
DEBUG addTreeItem: Folder 'Development' has 13 children
DEBUG loadFolders: Adding item 6: type=folder, name=WSL
DEBUG addTreeItem: Creating folder item with name='WSL', entry_id=2300636853632
DEBUG addTreeItem: Folder 'WSL' has 1 children
DEBUG loadFolders: Adding item 7: type=folder, name=Raspberry
DEBUG addTreeItem: Creating folder item with name='Raspberry', entry_id=2300636851392
DEBUG addTreeItem: Folder 'Raspberry' has 1 children
DEBUG loadFolders: Adding item 8: type=folder, name=Utilities
DEBUG addTreeItem: Creating folder item with name='Utilities', entry_id=2300636853568
DEBUG addTreeItem: Folder 'Utilities' has 5 children
DEBUG loadFolders: Adding item 9: type=separator, name=N/A
DEBUG loadFolders: Adding item 10: type=remainingProfiles, name=N/A
DEBUG loadFolders: Adding item 11: type=folder, name=New Folder
DEBUG addTreeItem: Creating folder item with name='New Folder', entry_id=2300636855872
DEBUG addTreeItem: Folder 'New Folder' has 0 children
DEBUG loadFolders: Tree now has 12 top-level items