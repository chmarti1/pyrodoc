var DEFAULT_IDSTR = "mp.H2O";
var infodata;

var unitModel;
var dataModel;

var unitPickerView;

var propEntryView;
var propChooserView;
var isolineChooserView;
var plotView;
var tableView;

// document.ready()
$(function(){
    let subid = config_substance();
    dataModel = new DataModel(subid);

    // ajax operation, so allow program flow to continue afterward
    async_info_request(()=>{
        config_units(()=>{
            config_modal_subsel();

            calc_auxline();

            propEntryView = new PropEntryView("property_controls",
                                                dataModel.get_input_properties(),
                                                unitModel.get_units_for_prop(dataModel.get_input_properties()),
                                                compute_point);


            propChooserView = new PropChooserView("property_selection", PropChooserView.EVENT_PROPERTY_VISIBILITY);
            isolineChooserView = new PropChooserView("isoline_selection", PropChooserView.EVENT_ISOLINE_VISIBILITY, ['T', 'd', 'p', 's', 'h', 'x']);
            propChooserView.init(dataModel.get_output_properties(), dataModel.DEFAULT_PROP_OUT_SHORTLIST);
            isolineChooserView.init(dataModel.get_output_properties(), ['T', 'p', 'x']);



            plotView = new PlotView("plot_display", dataModel, unitModel.get_units_for_prop, compute_point);
            dataModel.addListener(plotView);
            propChooserView.addListener(plotView);
            isolineChooserView.addListener(plotView);
            plotView.init();


            // Assign views to listen to the main model
            tableView = new TableView('property_table', dataModel, unitModel.get_units_for_prop);
            dataModel.addListener(tableView);
            propChooserView.addListener(tableView);
            tableView.init(dataModel.get_output_properties());

        });


    });
});


function config_modal_subsel(){
    $("#modal_substancepicker").load("../static/modal_substance.html", ()=>{
        sel_data_ready(infodata.data);
    });

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
function config_units(and_then){
    let actual = get_cookie("units");

    // If the unit data isn't set, initialize it.
    if (actual === ""){
        change_units(infodata.units);
    } else {
        actual = JSON.parse(actual);
    }
    unitPickerView = new UnitFormView('modal_unitspicker_content',
                                            "../static/unitspicker.html",
                                            infodata.data.legalunits,
                                            actual,
                                            infodata.units,
                                            apply_units,
                                            onclick_changeunits,
                                            and_then);
    unitModel = new UnitModel(infodata.data.legalunits, actual);
    display_units(actual);
}

function apply_units(units){
    $('#modal_unitspicker').toggle();
    change_units(units)
}

function async_info_request(and_then){
    // Make an async call to get the unit data
    return ajax_info((data) =>{
        infodata = data;
        and_then();
    });
}

function onclick_changesubstance(){
    $('#modal_substancepicker').toggle();
}


function onclick_changeunits(){
    $('#modal_unitspicker').toggle();
}

function change_substance(substance){
    set_cookie("idstr", substance);
    location.reload();
}

function change_units(units){
    set_cookie("units", JSON.stringify(units));
    location.reload();
}

function display_substance(sub){
    $("#sub_string").text(sub);
}

function display_units(units){
    $("#unit_string").text(JSON.stringify(units));
}

function ajax_info(callback){
    $.get("/info",
        callback,
        'json');  // Data type of the response.
}





function calc_auxline(){
    if (dataModel.get_substance().startsWith('mp')){
        compute_auxline((data)=>{
            let sll = data.data['liquid'];
            let svl = data.data['vapor'];
            // concatenate vapor to liquid
            Object.keys(svl).forEach(key => {
                for (let i = svl[key].length; i > -1; i--) {
                    sll[key].push(svl[key][i]);
                }
            });
            dataModel.add_auxline('steamdome', sll, parent='global');
        });

        compute_auxline((data)=>{
            data.data.data.forEach((line)=>{
                dataModel.add_auxline('x', line, 'global');
            });
        },{'x': 0, 'default': true});
    }

    // Add a few types of lines
    ['p', 'T', 'd', 'h', 's'].forEach((prop_val)=>{
        compute_args = {};
        compute_args[prop_val] = 0;
        compute_args["default"] = true;
        compute_auxline((data)=>{
            data.data.data.forEach((line)=>{
                dataModel.add_auxline(prop_val, line, 'global');
            });
        },compute_args);
    })
}



/**
 * Async request for getting a state from the backend.
 * @param callback - function handle to execute when complete
 * @param props - Dict with keys of property and numeric values
 * @param mode - GET/POST. Only POST can handle units with the request
 */
function compute_auxline(callback, props={}, mode="POST"){
    let requestroute;
    if (Object.keys(props).length === 0) {
        requestroute = "/saturation";
    } else {
        requestroute = "/isoline"
    }

    // Add the substance ID to props always
    props['id'] = dataModel.get_substance();

    if (mode === "GET"){
        $.get(requestroute, props, callback,dataType='json');
    } else if (mode === "POST") {
        let postData = Object.assign({}, props); // clone it
        postData.units = unitPickerView.get_values();  // add the units on
        $.ajax({
            url: requestroute,
            type: "POST",
            data: JSON.stringify(postData),
            dataType: "json",
            contentType: 'application/json; charset=utf-8',
            success: callback
        });
    }
}




/**
 * Async request for getting a state from the backend.
 * @param props - Dict with keys of property and numeric values
 * @param mode - GET/POST. Only POST can handle units with the request
 */
function compute_point(props){
    let requestroute = "/state";

    // Add the substance ID to props always
    props['id'] = dataModel.get_substance();

    // Build the data request
    let postData = Object.assign({}, props); // clone it
    postData.units = unitPickerView.get_values();  // add the units on
    $.ajax({
        url: requestroute,
        type: "POST",
        data: JSON.stringify(postData),
        dataType: "json",
        contentType: 'application/json; charset=utf-8',
        success: (data) =>{
                dataModel.add_point(data.data);
        },
    });
}
