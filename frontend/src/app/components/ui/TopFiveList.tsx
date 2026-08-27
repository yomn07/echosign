import { motion } from "motion/react";


type Candidate = {
  word:string;
  conf:number;
};


type Props = {

topWord:string;

topConf:number;

candidates:Candidate[];

};



export default function TopFiveList({

topWord,

topConf,

candidates

}:Props){


const list = [

{
word:topWord,
conf:topConf
},

...candidates.slice(0,4)

];



return (

<div className="
flex flex-col gap-2
">

{

list.map(

(item,index)=>{


const percent =
item.conf*100;


const main =
index===0;



return (

<div

key={
item.word+
index
}

className="
flex items-center gap-3
rounded-2xl
px-4 py-3
"

style={{

background:
main
?
"#EEF0FF"
:
"transparent",

border:
main
?
"1px solid #E2E0F8"
:
"1px solid transparent"

}}

>


<div

className="
w-7 h-7
rounded-full
flex items-center
justify-center
text-xs
font-bold
"

style={{

background:
main
?
"#6C47FF"
:
"#F5F4FF",

color:
main
?
"white"
:
"#B5A5FF"

}}

>

{index+1}

</div>





<div

className="
font-bold
w-28
"

style={{

color:
main
?
"#1A1535"
:
"#777"

}}

>

{item.word}

</div>





<div

className="
flex-1
rounded-full
overflow-hidden
"

style={{

height:
main
?
8
:
5,

background:"#F0EFFF"

}}

>


<motion.div

className="
h-full rounded-full
"

animate={{

width:`${percent}%`

}}

transition={{

duration:.5

}}

style={{

background:
main
?
"#6C47FF"
:
"#C4B0FF"

}}

/>


</div>





<span

className="
text-xs font-semibold
"

style={{

color:
main
?
"#6C47FF"
:
"#B5A5FF"

}}

>

{percent.toFixed(1)}%

</span>



</div>


);


}

)

}



</div>


);

}