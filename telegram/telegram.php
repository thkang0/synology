<?php
header("Content-Type: text/html; charset=utf-8");

define('BOT_TOKEN', $_GET["bot_token"]);
define('API_URL', 'https://api.telegram.org/bot'.BOT_TOKEN.'/');
 
// grab the chatID
$chatID = $_GET["chat_id"];
 
// compose reply
$reply =  sendMessage();
 
// send reply
$sendto = API_URL."sendmessage?chat_id=".$chatID."&text=".$reply;
file_get_contents($sendto);
 
function sendMessage(){
$message = urlencode($_GET["body"]);
return $message;
}
?>