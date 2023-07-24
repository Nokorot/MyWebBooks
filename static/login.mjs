let app = new Realm.App({ id: "royalroad-kyumk"});
const submit_button = document.querySelector("button[type='submit']");
submit_button.addEventListener("click", login());

async function login(){
    //get username and password
    const email = document.querySelector("#Username");
    const password = document.querySelector("#Password");
    const credentials = Realm.Credentials.emailPassword(email.value, password.value);

    // Authenticate the user
    const user = await app.logIn(credentials);
    
    // `App.currentUser` updates to match the logged in user
    console.assert(user.id === app.currentUser.id);
}