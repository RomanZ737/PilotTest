
//������ ������ CheckBox ����������� ������
let setMarkOpt = document.getElementById("id_test_name-set_mark")

if (setMarkOpt.checked == true) {
    $("#set_mark_comment").attr("style", "color: rgba(209, 209,209); font-size: 18px;");
}

setMarkOpt.addEventListener('change', SetMarkFunc); // ������ listener �� ������

function SetMarkFunc (event) {
    if (setMarkOpt.checked == true) {
        $("#set_mark_comment").attr("style", "color: rgba(209, 209,209); font-size: 18px;");
    } else {
        $("#set_mark_comment").attr("style", "color: rgba(209, 209,209, 0.4); font-size: 15px;");

        }
}
