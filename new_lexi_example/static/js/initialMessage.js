document.addEventListener('DOMContentLoaded', function () {

    // Add the initial message
    const initialMessage = `
    ### Welcome to Saucy's Employee Assistance Chatbot!

    I’m here to help you prepare our delicious menu items and assist you with any questions about running the restaurant. You can ask me how to cook specific dishes, prepare orders, or handle restaurant operations. Here are some examples of what you can ask:

    #### Cooking Instructions:
    - "How do I make Sweet Baby Baked Beans?"
    - "What’s the recipe for Green Chili Macaroni?"
    - "How do I cook ribs?"

    #### Preparing Orders:
    - "What comes with the Wing Plate?"
    - "How do I prepare a Three Meat Plate?"
    - "What sides go with the Hotlink Plate?"

    #### General Operations:
    - "How do I set up the grill for cooking hotlinks?"
    - "What’s the best way to season the catfish?"
    - "How do I clean the deep fryer?"

    #### Example Questions:
    - "Can you give me the recipe for Teriyaki Parmesan Corn?"
    - "How long should I bake the ribs?"
    - "What’s included in the Two Meat Plate?"

    Feel free to ask any questions you have, and I’ll provide you with the information you need to ensure our customers enjoy their meals. Let's get cooking!
    `;

    // Convert Markdown to HTML
    const htmlContent = marked.parse(initialMessage);

    // Set the content of the lexi-mark element
    document.getElementById('initial-message').innerHTML = htmlContent;


});

