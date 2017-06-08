#ifndef __CONSTRAINT_H
#define __CONSTRAINT_H
#include <entity.h>
#include <map>
#include <vector>
class constraint : public entity
{
private:
	static std::map<long, long> cookie2pkt;
	static std::map<long, long> cookie2dpid;
	int flow_id;
	std::vector<long> probe_cookies;
	bool eval_result;
	
public:
	constraint(int flow_id, bool eval_result);

	void add_probe_cookie(long cookie);

	static void put_statistics(long cookie, long pkt_count);

	static void put_cookie_dpid(long cookie, long dpid);

	virtual void print_out(std::ostream& os) const;

	virtual ~constraint();
};
#endif
