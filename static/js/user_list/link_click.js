// При нажатии кнопки "Фильтр", собираются данные из двух форм и отправляются на обработку
    // При таком виде возврата данных важно использовать для переменных только var а не let (во всех JS документа!!)
    $('#submitFilter').click(function() {
        var form_1 = $("#position_filter, #checkboxes").serialize();
        $.get("{% url 'quize737:user_list' %}", form_1, function(content){
            //console.log(form_1);
            //$("html").html(content);
            document.open();
            document.write(content);
            document.close();
            });
        });

    // При нажатии кнопки "Поиск", собираются данные из двух форм и отправляются на обработку
    // При таком виде возврата данных важно использовать для переменных только var а не let (во всех JS документа!!)
    $('#submitSearch').click(function() {
        var form_2 = $("#user_search, #checkboxes").serialize();
        $.get("{% url 'quize737:user_list' %}", form_2, function(content){
            document.open();
            document.write(content);
            document.close();
            });
        });

    // При нажатии кнопки "Сбросить Фильтр", собираются данные из двух форм и отправляются на обработку
    // При таком виде возврата данных важно использовать для переменных только var а не let (во всех JS документа!!)
    $('#resetFilterButton').click(function() {
        var form_3 = $("#checkboxes").serialize();
        $.get("{% url 'quize737:user_list' %}", form_3, function(content){
            document.open();
            document.write(content);
            document.close();
            });
        });

    // При нажатии кнопки "Назначить Тест", собираются данные из формы "checkboxes" и отправляются на обработку
    // При таком виде возврата данных важно использовать для переменных только var а не let (во всех JS документа!!)
    $('#assign_test_to_selected_users').click(function() {
        var form_4 = $("#checkboxes").serialize();
        $.get("{% url 'quize737:selected_users_test' %}", form_4, function(content){
            document.open();
            document.write(content);
            document.close();
            });
        });


    // При нажатии кнопки "Создать группу", собираются данные из формы "checkboxes" и отправляются на обработку
    // При таком виде возврата данных важно использовать для переменных только var а не let (во всех JS документа!!)
    $('#make_new_group_to_selected_users').click(function() {
        var form_5 = $("#checkboxes").serialize();
        $.get("{% url 'quize737:selected_users_new_group' %}", form_5, function(content){
            document.open();
            document.write(content);
            document.close();
            });
        });

    // При нажатии кнопки "Добавить в группу", собираются данные из формы "checkboxes" и отправляются на обработку
    // При таком виде возврата данных важно использовать для переменных только var а не let (во всех JS документа!!)
    $('#add_to_group_selected_users').click(function() {
        var form_6 = $("#checkboxes").serialize();
        $.get("{% url 'quize737:selected_users_add_to_group' %}", form_6, function(content){
            document.open();
            document.write(content);
            document.close();
            });
        });