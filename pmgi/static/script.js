
function getprops() {
    var xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var data = JSON.parse(this.responseText);
            var table = document.getElementById("proptable");
            var row = table.insertRow(table.rows.length-1);
            row.insertCell(0).innerHTML = data.T;
            row.insertCell(1).innerHTML = data.p;
            row.insertCell(2).innerHTML = data.d;
            row.insertCell(3).innerHTML = data.h;
            row.insertCell(4).innerHTML = data.s;
        }
    };
    var requeststr = "http://omnifariousbox.com/pmgi/?id=mp.H2O";
    requeststr += "&T=" + document.getElementById("Tinput").value;
    requeststr += "&p=" + document.getElementById("pinput").value;
    xhttp.open("GET", requeststr, true);
    xhttp.send();
}


function updateinputs() {
    // First, count the number of nonzero entries
    var count;
    var inputs = [document.getElementById("Tinput"), document.getElementById("pinput"), document.getElementById("dinput"), document.getElementById("hinput"), document.getElementById("sinput")];
    var x;
    
    count = 0;
    for (x of inputs){
        if (x.value.length){
            count += 1;
        }
    }
    
    if(count < 2){
        for (x of inputs){
            x.disabled = false;
        }
    }else{
        for (x of inputs){
            if (x.value.length==0){
                x.disabled = true;
            }
        }
    }
    
    // Then, grey out the entries that are zero (if appropriate)
}
