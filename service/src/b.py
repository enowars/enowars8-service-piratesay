# generate string like %18$llx.%19$llx %20$llx.%21$llx %22$llx.%23$llx %24$llx.%25$llx %26$llx.%27$llx %28$llx.%29$llx
# from starting value to end value
start_offset = 0
end_offset = 100
string = ""
for i in range(start_offset, end_offset + 1):
    string += f"%{i}$llx."
print(string)