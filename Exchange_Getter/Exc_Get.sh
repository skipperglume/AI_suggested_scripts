

searchstring1="CZK"
if [ -n "$1" ]
then
    searchstring1=$1
fi
searchstring2="UAH"
if [ -n "$2" ]
then
    searchstring2=$2
fi
if [[ $3 == "R" ]]; then
    rm ./currency-calculator.html
    wget  https://www.calculator.net/currency-calculator.html
    
fi
a=$(grep CZK currency-calculator.html)
rate1=${a#*$searchstring1}
rate1=${rate1#*$searchstring1}
rate1=${rate1:2:17}

non_digit=$(echo $rate1 | grep -o '[^0-9.]\+')

# echo $non_digit

if [ -n "$non_digit" ]
then
    rate1=${rate1%%$non_digit*}
fi
# echo $non_digit
echo "Dollar to $searchstring1 is 1 to $rate1"



rate2=${a#*$searchstring2}
rate2=${rate2#*$searchstring2}
rate2=${rate2:2:19}
non_digit=$(echo $rate2 | grep -o '[^0-9.]\+')
if [ -n "$non_digit" ]
then
    rate2=${rate2%%$non_digit*}
fi

echo "Dollar to $searchstring2 is 1 to $rate2"
final_rate=$(bc <<< "scale=5; $rate2/$rate1")
if [ ${final_rate:0:1} == '.' ]; then
    final_rate="0"$final_rate
fi
echo "1 $searchstring1 is $final_rate $searchstring2"


