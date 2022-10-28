var infodata
var substancePicker

$(function() {


    // Check if the infodata has been created. If not, get it from ajax and reload
    infodata = localStorage.getItem("infodata");
    if (infodata === null){
        ajax_info((data)=>{
            localStorage.setItem("infodata", JSON.stringify(data));
            infodata = data;
            init();
        });
    } else {
        infodata = JSON.parse(infodata);
        init();
    }
});

function init(){

    let subid = load_substance_choice();

    substancePicker = new ModalSubstancePicker('modal_substancepicker',
    '../static/modal_substance.html',
    infodata.data.substances);
    ajax_subst(subid, (data)=>{
        subst_data_ready(data);
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

function subst_data_ready(substdata){
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
    substancePicker.toggle();
}


function load_substance_choice(){
    let sub = get_cookie("idstr");
    if (sub === ""){
        change_substance(DEFAULT_IDSTR);
    } else {
        display_substance(sub);
    }
    return sub;
}

function display_substance(sub){
    $("#substance_title").text("Substance: "+sub);
}

function change_substance(substance){
    set_cookie("idstr", substance);
    location.reload();
}