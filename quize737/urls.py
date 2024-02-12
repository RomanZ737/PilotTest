from django.urls import path


from . import views
from PilotLoad import views as PLView
from django.conf import settings
from django.conf.urls.static import static



app_name = 'quize737'

urlpatterns = [
    path('', views.start, name='start'),
    path('go_back/', views.go_back_button, name='go_back_button'),
    path('<int:id>/', views.start, name='start'),
    path('next_question/', views.next_question, name='next_question'),
    path('tests_results_list/', views.tests_results_list, name='tests_results_list'),
    path('tests_results_list/<int:id>/', views.test_result_details, name='test_result_details'),
    path('question_list/', views.question_list, name='question_list'),
    path('question_list/<int:id>/', views.question_list_details, name='question_list_details'),
    path('new_question/', views.new_question, name='new_question'),
    path('download_test_result/<int:id>/', views.download_test_result, name='download_test_result'),
    path('test_editor/', views.test_editor, name='test_editor'),
    path('new_test_ac_type/', views.new_test_ac_type, name='new_test_ac_type'),
    path('create_new_test/', views.create_new_test, name='create_new_test'),
    path('test_editor/<int:id>/', views.test_details, name='test_details'),
    path('test_editor/del_test/<int:id>', views.del_test, name='del_test'),
    path('test_editor/<int:id>/del_test/', views.del_test, name='test_details'),
    path('user_list/', views.user_list, name='user_list'),
    path('group_list/', views.group_list, name='group_list'),
    path('group_list/<int:id>', views.group_list, name='group_list'),
    path('user_list/<int:id>', views.user_detales, name='user_detales'),
    path('file_upload/', views.file_upload, name='file_upload'),
    path('question_list/question_del/<int:id>', views.question_del, name='question_del'),
    path('question_list/<int:id>/question_del/', views.question_del, name='question_list'),
    path('theme_editor/', views.theme_editor, name='theme_editor'),
    path('theme_editor/<int:id>/', views.theme_editor, name='theme_editor'),
    path('theme_editor/<int:id>/theme_del/', views.theme_del, name='theme_del'),
    path('new_theme/', views.new_theme, name='new_theme'),
    path('question_form_file_download/', views.question_form_file_download, name='question_form_file_download'),
    path('group_users/<int:id>', views.group_users, name='group_users'),
    path('group_details/<int:id>', views.group_details, name='group_details'),
    path('new_group/', views.new_group, name='new_group'),
    path('group_list/<int:id>/group_del', views.group_del, name='group_del'),
    path('edit_user/<int:id>', views.edit_user, name='edit_user'),
    path('del_user/<int:id>', views.del_user, name='del_user'),
    path('new_user/', views.new_user, name='new_user'),
    path('edit_group/<int:id>', views.edit_group, name='edit_group'),
    path('pilotload/', PLView.pilotload, name='pilotload'),
    path('download_questions_bay/', views.download_questions_bay, name='download_questions_bay'),
    path('issue_mess/<int:id>', views.issue_mess, name='issue_mess'),
    path('mess_to_admin/', views.mess_to_admin, name='mess_to_admin'),
    path('selected_users_test/', views.selected_users_test, name='selected_users_test'),
    path('selected_users_new_group/', views.selected_users_new_group, name='selected_users_new_group'),
    path('selected_users_add_to_group/', views.selected_users_add_to_group, name='selected_users_add_to_group'),
    path('all_img_for_q_upload/<int:id>', views.all_img_for_q_upload, name='all_img_for_q_upload'),
    ]