var checkBox = document.querySelectorAll("input")  //Выбираем все объекты 'input'
    var optionsBlock = document.getElementById("inline_option_block")
    var paginator = document.getElementById("paginator") // Берем блок paginator


    for (i of checkBox) {  //перебираем в цикле все элементы 'checkbox'
        i.addEventListener('change', UserSelected);
        if (i.checked == true) { // Если пользователь устанавливает галку
                    optionsBlock.style.display = 'block';
                    if ( paginator != null) {
                        //console.log('paginator' + paginator);
                        paginator.style.display = 'none';
                       }

                    }
    }

    function UserSelected(event){
        event.preventDefault();
        if (event.target.checked == true) {
            if (optionsBlock.style.display == "none") {
            optionsBlock.style.display = 'block';
                if ( paginator != null) {
                    paginator.style.display = 'none'; // скрываем перелистывание страниц paginator
                }
            }
            } else {  //Если пользователь убирает галку, то проверяем есть ли ckeckbox с установленной галкой
                var boxFlag = false;
                for (i of checkBox) {
                    if (i.checked == true) {
                        boxFlag = true;
                        break;
                    }
                }
                if (boxFlag != true) {
                optionsBlock.style.display = 'none';
                if ( paginator != null) {
                    paginator.style.display = 'block';  // показываем перелистывание страниц paginator
                }
                }
        }
    }
