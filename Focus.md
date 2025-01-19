# Project Focus: 

**Current Goal:** Project directory structure and information

**Project Context:**
Type: Language: python
Target Users: Users of 
Main Functionality: Project directory structure and information
Key Requirements:
- Type: Python Project
- Language: python
- Framework: none
- File and directory tracking
- Automatic updates

**Development Guidelines:**
- Keep code modular and reusable
- Follow best practices for the project type
- Maintain clean separation of concerns

# 📁 Project Structure
├─ 📄 admin_utils.py (140 lines) - Python script containing project logic
├─ 📄 main.py (1505 lines) - Python script containing project logic
├─ 📄 setup_project.py (21 lines) - Python script containing project logic
├─ 📁 config
│  ├─ 📄 logging_config.py (9 lines) - Python script containing project logic
│  └─ 📄 settings.py (78 lines) - Python script containing project logic
├─ 📁 handlers
│  ├─ 📄 __init__.py (36 lines) - Python script containing project logic
│  ├─ 📄 admin.py (36 lines) - Python script containing project logic
│  ├─ 📄 admin_handlers.py (177 lines) - Python script containing project logic
│  ├─ 📄 broadcast.py (30 lines) - Python script containing project logic
│  ├─ 📄 callback_handlers.py (48 lines) - Python script containing project logic
│  ├─ 📄 chat_handlers.py (84 lines) - Python script containing project logic
│  ├─ 📄 command_handlers.py (93 lines) - Python script containing project logic
│  ├─ 📄 commands.py (43 lines) - Python script containing project logic
│  ├─ 📄 error_handler.py (48 lines) - Python script containing project logic
│  ├─ 📄 file_handlers.py (34 lines) - Python script containing project logic
│  ├─ 📄 file_ops.py (23 lines) - Python script containing project logic
│  ├─ 📄 settings_handlers.py (44 lines) - Python script containing project logic
│  └─ 📄 stats.py (34 lines) - Python script containing project logic
├─ 📁 services
│  ├─ 📄 ai_service.py (20 lines) - Python script containing project logic
│  ├─ 📄 backup_service.py (52 lines) - Python script containing project logic
│  ├─ 📄 chat_service.py (127 lines) - Python script containing project logic
│  ├─ 📄 file_service.py (47 lines) - Python script containing project logic
│  ├─ 📄 image_service.py (18 lines) - Python script containing project logic
│  ├─ 📄 language_service.py (35 lines) - Python script containing project logic
│  ├─ 📄 premium_service.py (39 lines) - Python script containing project logic
│  └─ 📄 user_service.py (110 lines) - Python script containing project logic
├─ 📁 utils
│  ├─ 📄 credits.py (44 lines) - Python script containing project logic
│  ├─ 📄 decorators.py (16 lines) - Python script containing project logic
│  └─ 📄 helpers.py (13 lines) - Python script containing project logic
└─ 📁 web
   └─ 📄 app.py (19 lines) - Python script containing project logic

# 🔍 Key Files with Methods

`handlers\admin.py` (36 lines)
Functions:
- admin_panel

`handlers\admin_handlers.py` (177 lines)
Functions:
- admin_dashboard
- error
- get_last_backup_date
- handle_admin_actions

`admin_utils.py` (140 lines)
Functions:
- UserCredits
- UserManager
- _load_credits
- _load_json
- _reset_credits
- _save_credits
- _save_json
- add_premium
- ban_user
- check_credits
- get_credits
- is_admin
- is_banned
- is_premium
- remove_premium
- unban_user
- use_credit

`services\ai_service.py` (20 lines)
Functions:
- AIService
- process_message

`web\app.py` (19 lines)
Functions:
- create_app

`services\backup_service.py` (52 lines)
Functions:
- BackupService
- _backup_directory
- create_backup

`handlers\broadcast.py` (30 lines)
Functions:
- bulunamadı
- collect_targets
- kullanıcıları
- send_broadcast

`handlers\callback_handlers.py` (48 lines)
Functions:
- handle_callback_query

`handlers\chat_handlers.py` (84 lines)
Functions:
- handle_chat
- is_admin

`services\chat_service.py` (127 lines)
Functions:
- ChatService
- clear_history
- get_ai_response
- get_history
- isinstance
- process_message
- save_message

`handlers\command_handlers.py` (93 lines)
Functions:
- add_thumbnail
- admin_panel
- ai_chat
- ai_clear
- ai_history
- delete_default_thumb
- get_image
- help_command
- start
- view_default_thumb

`handlers\commands.py` (43 lines)
Functions:
- start

`utils\credits.py` (44 lines)
Functions:
- check_credits
- update_credits

`utils\decorators.py` (16 lines)
Functions:
- decorator
- require_premium
- wrapper

`handlers\error_handler.py` (48 lines)
Functions:
- error_handler
- isinstance

`handlers\file_handlers.py` (34 lines)
Functions:
- process_file

`handlers\file_ops.py` (23 lines)
Functions:
- process_file

`services\file_service.py` (47 lines)
Functions:
- FileService
- process_image
- validate_filename

`utils\helpers.py` (13 lines)
Functions:
- save_json

`services\image_service.py` (18 lines)
Functions:
- ImageService
- search_image

`services\language_service.py` (35 lines)
Functions:
- LanguageService
- _load_translations
- get_text

`config\logging_config.py` (9 lines)
Functions:
- setup_logging

`main.py` (1505 lines)
Functions:
- ChatHistory
- _load_history
- _save_history
- add_message
- add_thumbnail
- admin_panel
- ai_chat
- ai_clear
- ai_history
- bulunamadı!
- cancel_admin_action
- channel_info
- check_membership
- clear
- decorator
- delete_default_thumb
- enhance_prompt
- error
- error_handler
- get_context
- get_image
- get_user_data
- glob
- handle_admin_actions
- handle_admin_callback
- handle_callback_query
- handle_rename_response
- handle_update
- hasattr
- home
- init_application
- için
- listesi
- locals
- main
- ping
- process_file
- rename_file
- require_credits
- run_flask
- save_default_thumb
- save_user_data
- setup_project
- setup_webhook
- start
- start_bot
- view_default_thumb
- webhook
- wrapper

`services\premium_service.py` (39 lines)
Functions:
- PremiumService
- add_premium

`handlers\settings_handlers.py` (44 lines)
Functions:
- settings_menu

`setup_project.py` (21 lines)
Functions:
- create_project_structure

`handlers\stats.py` (34 lines)
Functions:
- show_stats

`services\user_service.py` (110 lines)
Functions:
- UserService
- _create_default_stats
- get_active_users_today
- get_all_users
- get_premium_users
- get_total_users
- get_user_stats
- glob
- update_stats

# 📊 Project Overview
**Files:** 30  |  **Lines:** 3,023

## 📁 File Distribution
- .py: 30 files (3,023 lines)

*Updated: January 19, 2025 at 05:16 PM*