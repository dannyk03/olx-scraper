def main_1():
	global a
	global b
	global c

	print a, b, c
	a += 10

def main_2():
	global a
	global b
	global c
	
	print a
	b += 29

def main():
	global a
	global b
	global c

	a = 14
	b = 12
	c = 11
	main_1()
	main_2()

if __name__=="__main__":
	main()