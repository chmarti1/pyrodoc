var infodata
var substdata

$(function() {
    let subid = config_substance();
    async_info_request(()=>{
        config_modal_subsel();
        async_subst_request(subid, ()=>{
            subst_data_ready();
        });
    });
});


function async_info_request(and_then){
    // Make an async call to get the unit data
    return ajax_info((data) =>{
        infodata = data;
        and_then();
    });
}

function config_modal_subsel(){
    $("#modal_substancepicker").load("../static/modal_substance.html", ()=>{
        sel_data_ready(infodata.data);
    });
}

function async_subst_request(id, and_then){
    // Make an async call to get the unit data
    return ajax_subst(id, (data) =>{
        substdata = data;
        and_then();
    });
}

function ajax_info(callback){
    $.get("/info",
        callback,
        'json');  // Data type of the response.
}

function ajax_subst(id, callback){
    $.get("/subst?id="+id,
        callback,
        'json');  // Data type of the response.
}


//**********
// SUBST_XXX
// Substance page functions
//**********

function subst_data_ready(){
    // Parse the response and break it into its parts
    let data = substdata.data;
    let units = substdata.units;
    let formula = '';
    let qty = 0;
    let name, names='';
    let critical='', triple='';


    document.getElementById('subst_id').innerHTML = data['id'];
    document.getElementById('subst_col').innerHTML = data['col'];
    document.getElementById('subst_cls').innerHTML = data['cls'];
    document.getElementById('subst_mw').innerHTML = data['mw'] + ' ' + units['mass'] + '/' + units['molar'];
    document.getElementById('subst_inchi').innerHTML = data['inchi'];
    document.getElementById('subst_cas').innerHTML = data['casid'];

    for (atom in data['atoms']){
        qty = data['atoms'][atom];
        if (qty == 1){
            formula += atom;
        }else{
            formula += atom + '<sub>' + qty + '</sub>';
        }
    }
    document.getElementById('subst_form').innerHTML = formula;

    for (name of data['names']){
        names += name + '<br>'
    }
    document.getElementById('subst_names').innerHTML = names;
    document.getElementById('subst_doc').innerHTML = data['doc'];

    if (data['Tc'] != undefined){
        critical += data['Tc'] + ' ' + units['temperature'] + '<br>'
    }
    if (data['pc'] != undefined){
        critical += data['pc'] + ' ' + units['pressure'] + '<br>'
    }
    if (data['dc'] != undefined){
        critical += data['dc'] + ' ' + units['matter'] + '/' + units['volume'] + '<br>'
    }
    document.getElementById('subst_crit').innerHTML = critical;

    if (data['Tt'] != undefined){
        triple += data['Tt'] + ' ' + units['temperature'] + '<br>'
    }
    if (data['pt'] != undefined){
        triple += data['pt'] + ' ' + units['pressure'] + '<br>'
    }
    document.getElementById('subst_triple').innerHTML = triple;
}



function onclick_changesubstance(){
    $('#modal_substancepicker').toggle();
}

function config_substance(){
    let sub = get_cookie("idstr");
    if (sub === ""){
        change_substance(DEFAULT_IDSTR);
    } else {
        display_substance(sub);
    }
    return sub;
}

function display_substance(sub){
    $("#sub_string").text(sub);
}
function change_substance(substance){
    set_cookie("idstr", substance);
    location.reload();
}