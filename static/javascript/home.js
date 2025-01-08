var value1 = 0;
var value2 = 0;

function transition1(change) {
    element_val = document.getElementById("itemList1").getElementsByClassName("post").length;
    value1 = value1+change<0 ? 0 : value1+change>Math.abs(element_val-5)*200? value1 : value1+change;
    document.getElementById("itemList1").style.left = value1 + "px";
}

function transition2(change) {
    element_val = document.getElementById("itemList2").getElementsByClassName("post").length;
    value2 = value2+change<0 ? 0 : value2+change>Math.abs(element_val-5)*200? value2 : value2+change;
    document.getElementById("itemList2").style.left = value2 + "px";
}