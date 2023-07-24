//import * as Realm from "realm-web";
//const Realm = require("realm-web");

let app = new Realm.App({ id: "royalroad-kyumk"});
//const submit_button = document.querySelector("button[type='submit']");
//submit_button.addEventListener("click", register_user());
const form = document.querySelector("form");
form.addEventListener("submit", register_user());

async function register_user(){
    //get username and password
    const email = document.querySelector("#Username");
    const password = document.querySelector("#Password");

    const emailRegex = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
    if(email.value.match(emailRegex)){
        //create user
        try{
            await app.emailPasswordAuth.registerUser({ email: email.value, password: password.value });
        } catch(error){
            console.error(error);
        }
    } else {
        console.log("invalid email address");
        console.log(email.value);
        var paragraph = document.querySelector("p");
        paragraph.innerHTML = "invalid email address";
    }
}
